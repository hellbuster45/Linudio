#!/usr/bin/env bash
# Linux/macOS equivalent of Linudio.bat: sets up everything Linudio needs on a bare machine
# (system packages, the Python virtual environment, Node packages), starts the backend and
# frontend together, opens the browser once both are up, and shuts everything down when that
# tab is closed. The one thing this does NOT do is choose or download AI models - that stays a
# manual choice in the Settings panel once the app is running.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

# Linudio needs Python 3.11 specifically, not just "any python3". One of MeloTTS's pinned
# dependencies (an old transformers release, needed for compatibility) pulls in a tokenizers
# version that only ships a prebuilt wheel for Python 3.11. On Python 3.12+ (the default on
# Ubuntu 24.04, Fedora 40+, and other current distros) pip falls back to compiling it from Rust
# source, and that source is now too old to build with any current Rust compiler. Using 3.11
# avoids all of that rather than fighting it.
PYTHON=python3.11

# Next.js 16 needs Node >= 20.9. Ubuntu/Debian's own "nodejs" package is far older (18.x on
# Ubuntu 24.04) and not enough - that build gets installed separately, from NodeSource, below.
NODE_MAJOR=22

# ca-certificates is what lets pip, npm, and git make HTTPS requests at all. Most real systems
# already have it, but a bare/minimal install (e.g. a fresh container) will not.
# build-essential (gcc/g++/make) and libmecab-dev are needed to compile fugashi, the Japanese
# tokenizer MeloTTS depends on - pip cannot satisfy this one on its own.
SYSTEM_PACKAGES="git ffmpeg curl lsof ca-certificates build-essential mecab libmecab-dev mecab-ipadic-utf8"

# Root (e.g. inside a container) neither has nor needs sudo.
SUDO=sudo
[ "$(id -u)" = "0" ] && SUDO=""

install_system_packages() {
    echo "Installing required system packages ($SYSTEM_PACKAGES, plus Python 3.11)..."
    if command -v apt-get >/dev/null 2>&1; then
        # Without this, a dependency like tzdata can stop and ask an interactive question
        # (e.g. your timezone) that there is no terminal prompt to answer on a fresh install.
        $SUDO apt-get update
        $SUDO env DEBIAN_FRONTEND=noninteractive apt-get install -y $SYSTEM_PACKAGES software-properties-common
        if ! command -v python3.11 >/dev/null 2>&1; then
            # Ubuntu/Debian only ship the current release's Python as "python3" - 3.11 has to
            # come from the deadsnakes PPA (the standard, widely-used source for this).
            # python3.11-dev provides Python.h, needed to compile native extensions (e.g. diffq).
            $SUDO add-apt-repository -y ppa:deadsnakes/ppa
            $SUDO apt-get update
            $SUDO env DEBIAN_FRONTEND=noninteractive apt-get install -y python3.11 python3.11-venv python3.11-dev
        fi
        if ! command -v node >/dev/null 2>&1 || [ "$(node -e 'console.log(process.versions.node.split(".")[0])')" -lt "$NODE_MAJOR" ]; then
            # Ubuntu/Debian's own nodejs package is too old for Next.js; NodeSource is the
            # standard source for a current release on these distros.
            curl -fsSL "https://deb.nodesource.com/setup_${NODE_MAJOR}.x" | $SUDO -E bash -
            $SUDO env DEBIAN_FRONTEND=noninteractive apt-get install -y nodejs
        fi
        $SUDO update-ca-certificates
    elif command -v dnf >/dev/null 2>&1; then
        # Fedora's package is just "python3-pip"; ffmpeg needs RPM Fusion, which we won't add on
        # the user's behalf, so this can leave ffmpeg missing - the preflight check below will
        # say so if that happens. Fedora's nodejs package is current enough, unlike Ubuntu's.
        $SUDO dnf install -y python3.11 python3.11-devel nodejs npm git ffmpeg curl lsof ca-certificates gcc gcc-c++ make mecab mecab-devel mecab-ipadic || \
            $SUDO dnf install -y python3.11 python3.11-devel nodejs npm git curl lsof ca-certificates gcc gcc-c++ make mecab mecab-devel mecab-ipadic
    elif command -v pacman >/dev/null 2>&1; then
        # Arch only packages the current Python release; building 3.11 from the AUR is out of
        # scope for an unattended script, so this is the one case where we fall back. Arch's
        # python and nodejs packages are both current enough as-is.
        # (Arch's python package includes headers, so no separate -dev package is needed.)
        $SUDO pacman -Sy --noconfirm python python-pip nodejs npm git ffmpeg curl lsof ca-certificates base-devel mecab mecab-ipadic
        PYTHON=python3
        echo "Warning: could not install Python 3.11 specifically on Arch; using the system python3."
        echo "If a later step fails to build 'tokenizers', install Python 3.11 yourself (e.g. via pyenv) and re-run."
    elif command -v brew >/dev/null 2>&1; then
        brew install python@3.11 node git ffmpeg curl lsof mecab mecab-ipadic
        PYTHON=python3.11
    else
        echo "Could not detect a supported package manager (apt, dnf, pacman, or Homebrew)."
        echo "Install these yourself, then run this script again: Python 3.11 (with venv and pip), node, npm, git, ffmpeg, curl, lsof"
        exit 1
    fi
}

missing=()
for cmd in "$PYTHON" node npm git ffmpeg curl lsof; do
    command -v "$cmd" >/dev/null 2>&1 || missing+=("$cmd")
done
# A "node" that exists but is too old for Next.js counts as missing too.
if command -v node >/dev/null 2>&1 && [ "$(node -e 'console.log(process.versions.node.split(".")[0])')" -lt "$NODE_MAJOR" ]; then
    missing+=("node (too old)")
fi
if [ "${#missing[@]}" -gt 0 ]; then
    echo "Missing: ${missing[*]}"
    install_system_packages
fi
# The venv module doesn't put anything new on PATH, so check it the only way that actually works.
if ! "$PYTHON" -c "import venv" >/dev/null 2>&1; then
    install_system_packages
fi

# Set up the virtual environment and install the backend the first time this runs.
VENV=backend/venv
if [ -f "$VENV/bin/activate" ]; then
    : # already set up
elif [ -f "backend/.venv/bin/activate" ]; then
    VENV=backend/.venv
else
    echo "Setting up the Python virtual environment..."
    "$PYTHON" -m venv "$VENV"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"

if ! python -c "import fastapi" >/dev/null 2>&1; then
    echo "Installing backend dependencies (this downloads several GB and can take a while)..."
    (cd backend && python install.py)
fi

free_ports() {
    # Close anything left over from a previous run (the API on 8000, the web UI on 3000).
    for port in 8000 3000; do
        pid=$(lsof -ti tcp:"$port" 2>/dev/null || true)
        [ -n "$pid" ] && kill -9 $pid 2>/dev/null || true
    done
}
free_ports

# First run: install the Node packages (root tooling, then the frontend).
if [ ! -d "node_modules" ]; then
    echo "Installing Node packages..."
    npm install
fi
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend packages..."
    (cd frontend && npm install)
fi

# Open the browser as soon as both servers answer. Runs in the background.
(
    deadline=$((SECONDS + 300))
    for url in http://localhost:8000 http://localhost:3000; do
        while [ "$SECONDS" -lt "$deadline" ]; do
            curl -sf -o /dev/null "$url" && break
            sleep 1
        done
    done
    if command -v xdg-open >/dev/null 2>&1; then
        xdg-open http://localhost:3000 >/dev/null 2>&1
    elif command -v open >/dev/null 2>&1; then
        open http://localhost:3000
    fi
) &

# Tells the backend to stop itself (and with it, everything) once the last browser tab is closed.
export LINUDIO_EXIT_ON_CLOSE=1

echo "Starting Linudio. Close the browser tab to stop it."
npm run dev

# Normally reached after the tab is closed; make sure nothing is left behind.
free_ports
