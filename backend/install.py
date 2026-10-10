"""Installs the Linudio backend dependencies in the order they have to be installed.

    python install.py              # CPU-only PyTorch (works everywhere)
    python install.py --gpu        # NVIDIA GPU build of PyTorch (CUDA 12.1)
    python install.py --postgres   # also install the PostgreSQL driver

Run it with the Python you want Linudio to use, inside a virtual environment.

Why not just `pip install -r requirements.txt`? audio-separator and MeloTTS declare
incompatible dependency ranges (librosa, numpy, torch), so pip's resolver refuses to install
both at once. The steps below pin the stack MeloTTS needs and install audio-separator without
its own dependency resolution. See requirements-separator.txt.
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TORCH_VERSION = "2.2.2"
TORCH_INDEX = {
    "cpu": "https://download.pytorch.org/whl/cpu",
    "gpu": "https://download.pytorch.org/whl/cu121",
}
AUDIO_SEPARATOR = "audio-separator==0.44.1"
NLTK_PACKAGES = ["averaged_perceptron_tagger_eng", "cmudict"]
NLTK_DIR = HERE.parent / "models" / "nltk_data"
KOREAN_PACKAGE = "eunjeon" if sys.platform == "win32" else "python-mecab-ko"

def pip(*args: str) -> None:
    command = [sys.executable, "-m", "pip", *args]
    print(f"\n$ {' '.join(command)}", flush=True)
    subprocess.run(command, check=True, cwd=HERE)

def main() -> int:
    parser = argparse.ArgumentParser(description="Install the Linudio backend dependencies.")
    parser.add_argument("--gpu", action="store_true", help="install the CUDA 12.1 build of PyTorch instead of CPU")
    parser.add_argument("--postgres", action="store_true", help="also install the PostgreSQL driver")
    parser.add_argument("--allow-global", action="store_true", help="install even when not inside a virtual environment")
    args = parser.parse_args()

    if sys.prefix == sys.base_prefix and not args.allow_global:
        print(
            "This Python is not inside a virtual environment, and Linudio pins specific versions of\n"
            "several libraries that would replace whatever you have installed.\n\n"
            "Create and activate one first:\n"
            "    python -m venv venv\n"
            "    venv\\Scripts\\activate        (Windows)\n"
            "    source venv/bin/activate      (Linux / macOS)\n\n"
            "or re-run with --allow-global if you really want to install into this Python."
        )
        return 1

    if sys.version_info[:2] not in ((3, 10), (3, 11)):
        print(f"Warning: Linudio is tested on Python 3.11; you are running {sys.version.split()[0]}.")

    if shutil.which("git") is None:
        print("git was not found on your PATH. It is needed to install MeloTTS from GitHub.")
        return 1

    torch_index = TORCH_INDEX["gpu" if args.gpu else "cpu"]

    # 1. PyTorch first, from the right index, so later steps don't pull in a different build.
    pip("install", f"torch=={TORCH_VERSION}", f"torchaudio=={TORCH_VERSION}", "--index-url", torch_index)
    # 2. The app itself, MeloTTS, faster-whisper, etc.
    pip("install", "-r", "requirements.txt")
    # 3. What audio-separator needs, held to the tested stack.
    pip("install", "-r", "requirements-separator.txt", "-c", "constraints.txt")
    # 4. audio-separator itself, without letting it change the stack.
    pip("install", "--no-deps", AUDIO_SEPARATOR)
    if args.postgres:
        pip("install", "-r", "postgres/requirements-postgres.txt")
    # 5. MeloTTS can't even be imported without UniDic's dictionary data (a separate ~0.8 GB download).
    check_dictionary = [sys.executable, "-c",
                        "import sys; sys.path.insert(0, '.'); from core.preflight import japanese_dictionary_ready as ok; sys.exit(0 if ok() else 1)"]
    if subprocess.run(check_dictionary, cwd=HERE).returncode != 0:
        print("\nDownloading the UniDic dictionary that MeloTTS needs (about 0.8 GB)...", flush=True)
        subprocess.run([sys.executable, "-m", "unidic", "download"], check=True, cwd=HERE)
    # 6. MeloTTS' English speech needs nltk data that newer nltk no longer fetches for it. Kept in
    #    models/ with everything else the app downloads (main.py points NLTK_DATA there).
    NLTK_DIR.mkdir(parents=True, exist_ok=True)
    print("\nDownloading English text-processing data...", flush=True)
    subprocess.run([sys.executable, "-m", "nltk.downloader", "-d", str(NLTK_DIR), *NLTK_PACKAGES], check=True, cwd=HERE)
    # 7. Optional: Korean dubbing. On Windows this usually has to be compiled, which fails without
    #    the Microsoft C++ Build Tools, so a failure here is a warning, not an error.
    print(f"\nInstalling the optional Korean text-to-speech tokenizer ({KOREAN_PACKAGE})...", flush=True)
    korean = subprocess.run([sys.executable, "-m", "pip", "install", KOREAN_PACKAGE], cwd=HERE)
    if korean.returncode != 0:
        print(f"\nCould not install {KOREAN_PACKAGE}, so dubbing into Korean will not work. Everything else is fine.\n"
              "On Windows, install the Microsoft C++ Build Tools and run `pip install eunjeon` to enable it.")

    print("\nDependencies installed. Checking for the system tools Linudio needs...\n")
    sys.path.insert(0, str(HERE))
    os.environ.setdefault("NLTK_DATA", str(NLTK_DIR))  # same place main.py points the app at
    from core.preflight import check_system

    report = check_system()
    for check in report["checks"]:
        label = "ok" if check["ok"] else ("optional" if check["optional"] else "MISSING")
        print(f"  [{label}] {check['name']}" + ("" if check["ok"] else f"  ->  {check['hint']}"))

    print("\nNext: start the backend with `uvicorn main:app`, then open the settings panel in the UI.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
