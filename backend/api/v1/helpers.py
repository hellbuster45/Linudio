from pathlib import Path
from yt_dlp import YoutubeDL
import os, re

def downloader(url: str):
    try: 
        save_path = Path(__file__).resolve().parents[4] / "storage"
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',      # WAV is uncompressed and faster to read
            }],
            'postprocessor_args': [
                '-ar', '16000',               # Audio Rate: 16kHz
                '-ac', '1'                    # Audio Channels: 1 (Mono)
            ],
            'outtmpl': f'storage/audio/%(id)s.%(ext)s',
            'quiet': True,
        }

        with YoutubeDL(ydl_opts) as ydl: # download audio, return file path
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info).replace('.webm', '.wav').replace('.m4a', '.wav')
            return { 
                "file_path": file_path,
            }
    except Exception as e:
        print(f"Downloader Error: {str(e)}")
        print(f"Metadata fetched: {info}")
        return {
            'location' : 'HELPERS',
            'error'    : str(e)
        }

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
