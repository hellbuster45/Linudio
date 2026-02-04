from pathlib import Path
from yt_dlp import YoutubeDL
import os, subprocess

def downloader(url: str):
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

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info).replace('.webm', '.wav').replace('.m4a', '.wav')
        return file_path

def get_metadata(url: str):
    options = {
        "quiet": True,
        "js-runtime": {"node": {}}
    }
    
    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(url=url, download=False)
    
    print(info.keys())
    
    return {
        "title": info.get("title"),
        "thumbnail": info.get("thumbnail"),
        "duration": info.get("duration"),
        "upload_date": info.get("upload_date"),
        "resolution": info.get("resolution"),
        "fps": info.get("fps")
    }