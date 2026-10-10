from yt_dlp import YoutubeDL
import os, re, asyncio, shutil, sys
from urllib.parse import parse_qs, urlparse
from core.config import settings
from core.proc import run_command
from core.validation import is_valid_video_id

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

def _ydl_base_opts() -> dict:
    opts = {
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'quiet': True,
        'no_warnings': False,
        'no_playlist': True,
        # yt-dlp needs a JavaScript runtime to solve YouTube's player challenges.
        # It uses whichever of these is installed (deno is recommended).
        'js_runtimes': {'deno': {}, 'node': {}},
        'remote_components': ['ejs:github'],
    }
    # Optional: a Netscape-format cookies.txt in the storage folder lets yt-dlp
    # download age-restricted or "confirm you're not a bot" videos.
    if settings.cookies_file.is_file():
        opts['cookiefile'] = str(settings.cookies_file)
    return opts

async def downloader(url: str, video_id: str):
    try:
        # Each video lives in <storage>/videos/<video_id>
        base_path = str(settings.videos_dir / video_id)
        os.makedirs(base_path, exist_ok=True)

        master_video = os.path.join(base_path, f"{video_id}_video.mp4")
        stereo_audio = os.path.join(base_path, f"{video_id}_stereo.wav")
        mono_audio   = os.path.join(base_path, f"{video_id}_mono.wav")

        ydl_opts = {
            **_ydl_base_opts(),
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': master_video,
        }

        def _download():
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        # yt-dlp is blocking; run it off the event loop so the API stays responsive.
        await asyncio.to_thread(_download)

        ffmpeg_cmd = [
            'ffmpeg', '-y', '-i', master_video,
            '-map', '0:a:0', '-ac', '2', '-ar', '44100', stereo_audio,
            '-map', '0:a:0', '-ac', '1', '-ar', '16000', mono_audio,
        ]

        result = await run_ffmpeg(ffmpeg_cmd, "Audio-Split")

        if result == 0 and os.path.exists(stereo_audio) and os.path.exists(mono_audio):
            return {
                'folder': base_path,
                'files': {
                    'video': master_video,
                    'stereo': stereo_audio,
                    'mono': mono_audio,
                },
            }
        return {
            "status": "error",
            "location": "HELPERS",
            "error": "FFMpeg failed to create required files"
        }
    except Exception as e:
        return {
            'location' : 'HELPERS',
            'error'    : str(e)
        }

async def run_ffmpeg(cmd_list, task_name="FFMpeg"):
    ffmpeg_exe = shutil.which("ffmpeg")
    if not ffmpeg_exe:
        print(f"[{task_name}] ERROR: ffmpeg not found in PATH.")
        return -1

    returncode, _ = await run_command([ffmpeg_exe, *cmd_list[1:]], task_name)
    return returncode

_YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be", "www.youtu.be"}

def is_youtube_url(url: str) -> bool:
    """yt-dlp will happily fetch hundreds of other sites (and local addresses), so only
    YouTube links are accepted, and this is checked before anything touches the network."""
    try:
        parsed = urlparse(url if "://" in url else f"https://{url}")
    except ValueError:
        return False
    return parsed.scheme in ("http", "https") and (parsed.hostname or "").lower() in _YOUTUBE_HOSTS

def get_metadata(url: str):
    try:
        video_id = extract_youtube_id(url) if is_youtube_url(url) else None
        if video_id is None:
            return {
                'location': 'HELPERS-METADATA',
                'error': "That doesn't look like a YouTube video link."
            }

        with YoutubeDL(_ydl_base_opts()) as ydl:
            print(f"Fetching metadata for URL: {url}")
            info = ydl.extract_info(url=url, download=False)

        return {
            "video_id"    : video_id,
            "title"       : info.get("title"),
            "thumbnail"   : info.get("thumbnail"),
            "duration"    : info.get("duration"),
            "upload_date" : info.get("upload_date"),
            "resolution"  : info.get("resolution"),
            "fps"         : info.get("fps")
        }
    except Exception as e:
        print(f"Metadata Error: {str(e)}")
        return {
            'location': 'HELPERS-METADATA',
            'error': str(e)
        }

def extract_youtube_id(url: str) -> str | None:
    """Returns the 11-character video id from a YouTube link, or None if there isn't a valid one.
    Handles watch?v=, youtu.be/, /embed/, /v/, /shorts/ and /live/ links."""
    try:
        parsed = urlparse(url if "://" in url else f"https://{url}")
    except ValueError:
        return None

    host = (parsed.hostname or "").lower()
    if host in ("youtu.be", "www.youtu.be"):
        candidate = parsed.path.lstrip("/").split("/")[0]
    else:
        candidate = (parse_qs(parsed.query).get("v") or [None])[0]
        if not candidate:
            match = re.match(r"^/(?:embed|v|shorts|live)/([^/?#]+)", parsed.path)
            candidate = match.group(1) if match else None

    return candidate if is_valid_video_id(candidate) else None
