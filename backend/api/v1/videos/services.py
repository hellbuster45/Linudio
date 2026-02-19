from pathlib import Path
from yt_dlp import YoutubeDL
import os, re
from .models import Transcripts
from sqlalchemy.exc import SQLAlchemyError

def get_or_create_transcript(db, video_url):
    try: # get video_id and transcripts, if present
        print("\nInside get or create function\n")
        video_id = extract_youtube_id(url=video_url)
        print("\n ID Extracted\n")
        transcript_obj = db.query(Transcripts).filter_by(video_id=video_id).first()
        print("\n DB query to check transcript\n")

        if transcript_obj and transcript_obj.transcript: # return transcript if video already processed
            return transcript_obj.transcript
        print("\n No transcript\n")
        
        print("\n Starting Video Download!! \n")
        video_info = downloader(url=video_url) # download video, if no transcript available
        print("\n Video Downloaded!! \n")
        try: 
            video_row = Transcripts(
                video_id=video_id,
                video_title=video_info["title"],
                thumbnail_url=video_info["thumbnail"],
                audio_path=video_info["file_path"]
            )
            db.add(video_row)
            db.commit()
            db.refresh(video_row) # add new transcript into database
            print("\n Video data added to DB!! \n")
        except SQLAlchemyError as e:
            db.rollback()
            return {"error": f"Database Insert Failed, {str(e)}"}
    except Exception as e:
        return {"error": str(e)}
    else:
        return {"message": "Success"}

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

        with YoutubeDL(ydl_opts) as ydl: # download video and return required metadata, along with file path
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info).replace('.webm', '.wav').replace('.m4a', '.wav')
            return { 
                "file_path": file_path,
                "title": info.get("title"),
                "thumbnail": info.get("thumbnail"),
                "duration": info.get("duration"),
                "upload_date": info.get("upload_date"),
                "resolution": info.get("resolution"),
                "fps": info.get("fps")
            }
    except Exception as e:
        return {"error": str(e)}


def get_metadata(url: str):
    options = {
        "quiet": True,
        "js-runtime": {"node": {}}
    }
    
    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(url=url, download=False)
    
    print(info.keys())
    
    return {
        "video_id": extract_youtube_id(url),
        "title": info.get("title"),
        "thumbnail": info.get("thumbnail"),
        "duration": info.get("duration"),
        "upload_date": info.get("upload_date"),
        "resolution": info.get("resolution"),
        "fps": info.get("fps")
    }

def extract_youtube_id(url: str) -> str | None:
    reg_exp = re.compile(r'^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#\&\?]*).*')
    match = reg_exp.match(url)
    if match and len(match.group(7)) == 11:
        return match.group(7)
    return None
