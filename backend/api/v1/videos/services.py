from .models import Videos
from sqlalchemy.exc import SQLAlchemyError
from ..helpers import downloader

async def get_video(video_url, db, metadata):
    try: # get video_id, and transcripts if present
        video_id = metadata['video_id']
        video_info = await downloader(url=video_url, video_id=video_id) # download video, if no transcript available
        print("\n\n\nVIDEO_INFO\n\n\n", video_info)
        print(f"\n\nAUDIO_PATH: { video_info.get('folder') }\n\n")
        try:
            video_row = Videos(
                video_id      = video_id,
                video_title   = metadata["title"],
                thumbnail_url = metadata["thumbnail"],
                audio_path    = video_info["folder"]
            )
            db.add(video_row)
            db.commit()
            db.refresh(video_row) # add new video data into database
        except SQLAlchemyError as e:
            return {
                'location' : 'VIDEOS-SERVICES',
                'error'    : f"Database Insert Failed => {str(e)}"
            }
        finally:
            db.close()
            
    except Exception as e:
        return {
            'location' : 'VIDEOS-SERVICES',
            'error'    : str(e)
        }
    else:
        return {"message": "Success"}

def start_transcript_generation(audio_file_path: str):
    pass