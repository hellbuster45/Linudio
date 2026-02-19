from .models import Transcripts
from sqlalchemy.exc import SQLAlchemyError
from ..helpers import downloader, extract_youtube_id

def get_transcript(db, video_url):
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

def start_transcript_generation(audio_file_path: str):

    pass