import importlib.util
import os
import shutil
import sys

# nltk resources MeloTTS' English text processing needs. Recent nltk versions renamed the
# tagger, and MeloTTS only fetches the old name, so English synthesis fails without these.
NLTK_RESOURCES = ("averaged_perceptron_tagger_eng", "cmudict")
_NLTK_PATHS = {"averaged_perceptron_tagger_eng": "taggers/averaged_perceptron_tagger_eng", "cmudict": "corpora/cmudict"}

def japanese_dictionary_ready() -> bool:
    """MeloTTS loads MeCab with the full `unidic` dictionary when that package is installed,
    but the package ships without the dictionary data (a separate ~0.8 GB download). Without
    it the TTS worker crashes on startup with a cryptic MeCab error."""
    try:
        import unidic
    except ImportError:
        return True  # MeCab falls back to the small bundled unidic-lite
    return os.path.isfile(os.path.join(unidic.DICDIR, "mecabrc"))

def english_speech_data_ready() -> bool:
    try:
        import nltk
    except ImportError:
        return True
    for resource in NLTK_RESOURCES:
        try:
            nltk.data.find(_NLTK_PATHS[resource])
        except LookupError:
            return False
    return True

def korean_tokenizer_ready() -> bool:
    """Korean text-to-speech needs a Korean MeCab build: `eunjeon` on Windows (which often has
    to be compiled, needing the Microsoft C++ Build Tools) and `python-mecab-ko` elsewhere."""
    module = "eunjeon" if sys.platform == "win32" else "mecab"
    return importlib.util.find_spec(module) is not None

def check_system() -> dict:
    """Checks for the external tools Linudio shells out to. These are system installs,
    not pip packages, so a missing one only shows up later as a confusing mid-job error.
    Checks marked `optional` only disable one feature; the rest only count the others."""
    checks = [
        {
            "name": "ffmpeg",
            "ok": shutil.which("ffmpeg") is not None,
            "optional": False,
            "hint": "Install FFmpeg and make sure `ffmpeg` is on your PATH.",
        },
        {
            "name": "ffprobe",
            "ok": shutil.which("ffprobe") is not None,
            "optional": False,
            "hint": "Install FFmpeg (it includes ffprobe) and make sure `ffprobe` is on your PATH.",
        },
        {
            "name": "JavaScript runtime (Deno or Node.js)",
            "ok": shutil.which("deno") is not None or shutil.which("node") is not None,
            "optional": False,
            "hint": "Install Deno (recommended) or Node.js so yt-dlp can download from YouTube.",
        },
        {
            "name": "Japanese dictionary for text-to-speech (unidic)",
            "ok": japanese_dictionary_ready(),
            "optional": False,
            "hint": "Run `python -m unidic download` (about 0.8 GB). Without it, dubbing fails to start.",
        },
        {
            "name": "English text-to-speech data (nltk)",
            "ok": english_speech_data_ready(),
            "optional": False,
            "hint": "Run `python install.py` again, or `python -m nltk.downloader -d ../models/nltk_data averaged_perceptron_tagger_eng cmudict`.",
        },
        {
            "name": "Korean text-to-speech tokenizer",
            "ok": korean_tokenizer_ready(),
            "optional": True,
            "hint": "Only needed to dub into Korean. Install `eunjeon` (Windows; needs the Microsoft C++ Build Tools) or `python-mecab-ko` (Linux / macOS).",
        },
    ]
    return {"ok": all(c["ok"] for c in checks if not c["optional"]), "checks": checks}

def print_preflight_warnings() -> None:
    for check in check_system()["checks"]:
        if not check["ok"]:
            kind = "Optional, missing" if check["optional"] else "Missing"
            print(f"[PREFLIGHT] {kind}: {check['name']}. {check['hint']}")
