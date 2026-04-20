from pathlib import Path
from yt_dlp import YoutubeDL
import os, re, asyncio, shutil,sys, traceback

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

async def downloader(url: str, video_id: str):
    try:
        # Create Path for each video storage/{video_id}
        base_path = os.path.join("storage", video_id)
        os.makedirs(base_path, exist_ok=True)

        master_video = os.path.join(base_path, f"{video_id}_video.mp4")
        stereo_audio = os.path.join(base_path, f"{video_id}_stereo.wav")
        mono_audio   = os.path.join(base_path, f"{video_id}_mono.wav")
        
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'quiet': True,
            'outtmpl': master_video,
            "javascript_runtimes": ['deno'],
            'remote_components': ['ejs:github'],

            'enable_ejs': True,
            'cookiefile': 'storage/cookies.txt',
            'nocheckcertificate': True,
            'no_warnings': False,
            'no_playlist': True,
        }

        with YoutubeDL(ydl_opts) as ydl: # download audio, return file path
            ydl.download([url])
        
        ffmpeg_cmd = [
            'ffmpeg', '-y', '-i', master_video,
            '-map', '0:a:0', '-ac', '2', '-ar', '44100', stereo_audio,
            '-map', '0:a:0', '-ac', '1', '-ar', '16000', mono_audio,
        ]

        result = await run_ffmpeg(ffmpeg_cmd, "Audio-Split")

        if result == 0:
            if os.path.exists(stereo_audio) and os.path.exists(mono_audio):
                return {
                    'folder': base_path,
                    'files': {
                        'video': master_video,
                        'stereo': stereo_audio,
                        'mono': mono_audio,
                    },
                }
        else:
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
    try:
        # 1. Verify FFmpeg exists
        ffmpeg_exe = shutil.which("ffmpeg")
        if not ffmpeg_exe:
            print(f"[{task_name}] ERROR: ffmpeg.exe not found in PATH.")
            return -1

        # 2. Build the command string properly
        # We wrap paths in quotes to handle Windows spaces
        formatted_args = []
        for arg in cmd_list:
            arg_str = str(arg)
            if " " in arg_str or "\\" in arg_str:
                formatted_args.append(f'"{arg_str}"')
            else:
                formatted_args.append(arg_str)
        
        cmd_str = " ".join(formatted_args)
        
        print(f"--- Executing: {cmd_str} ---")

        # 3. Create the subprocess
        # Pass ONLY the string as the first argument, others as keywords
        process = await asyncio.create_subprocess_shell(
            cmd_str,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        print(f"--- Subprocess Created (PID: {process.pid}) ---")

        # 4. Monitor stderr (where FFmpeg output lives)
        async def stream_logs(stream):
            while True:
                line = await stream.readline()
                if not line:
                    break
                # Use replace to handle Windows console encoding issues
                print(f"[{task_name}] {line.decode('utf-8', errors='replace').strip()}")

        # Run logging and wait for exit
        await asyncio.gather(
            stream_logs(process.stderr),
            process.wait()
        )

        return process.returncode

    except Exception:
        print(f"CRITICAL ERROR in {task_name}:")
        print(traceback.format_exc())
        return -1

def get_metadata(url: str):
    try:
        options = {
            "quiet": True,
            "js-runtime": {"node": {}}
        }
        
        with YoutubeDL(options) as ydl:
            print(f"Fetching metadata for URL: {url}")
            info = ydl.extract_info(url=url, download=False)
        
        return {
            "video_id"    : extract_youtube_id(url),
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
    reg_exp = re.compile(r'^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#\&\?]*).*')
    match = reg_exp.match(url)
    if match and len(match.group(7)) == 11:
        return match.group(7)
    return None
