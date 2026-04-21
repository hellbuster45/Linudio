import os, asyncio
from audio_separator.separator import Separator
from sqlalchemy.exc import SQLAlchemyError

output_dir = "storage/stems"
separator = Separator(output_dir=output_dir)
separator.load_model('UVR-MDX-NET-Voc_FT.onnx')

async def seperate_dialogues_background(video_id, db):
    try:
        output_files = await asyncio.to_thread(separator.separate, f"storage/{video_id}/{video_id}_stereo.wav")

        background_file = next((f for f in output_files if "Instrumental" in f), None)

        if not background_file:
            return {
                "status": "error",
                "error": "Background Track not in output_files!"
            }
        
        bg_file_path = os.path.join(output_dir, background_file)

        print(f"--- Background SFX File ready at {bg_file_path} ---")
        return {
            "status": "success"
        }
    except SQLAlchemyError as e:
        return {
            "status": "error",
            "error": str(e)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }