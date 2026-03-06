import whisper
import os, time

model = whisper.load_model("base", device="cpu")

def transcribe_audio(file_path: str):
    if not os.path.exists(file_path):
        return {"error": "FILE NOT FOUND !!"}
    try:
        print("\n\nTranscription Started !!\n\n")
        start_time = time.time()
        result = model.transcribe(file_path, fp16=False)
        end_time = time.time()
        print("\n\n Time Taken: ", end_time-start_time)
        print("\n\n")
        return {"result": result["text"].strip()}
    except:
        return {"error": "ERROR IN TRANSCRIPTION !!"}