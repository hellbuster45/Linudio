from faster_whisper import WhisperModel
import os, time

try:
    model = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
except Exception as e:
    print({
        'location': "TRANSCRIPTION",
        'error'   : e
    })

def transcribe_audio(file_path: str):
    if not os.path.exists(file_path):
        return {
            'location' : 'TRANSCRIPTION',
            'error': "FILE NOT FOUND !!"
        }
    
    try:
        print("\n\nTranscription Started !!\n\n")
        start_time = time.time()
        
        segments, info = model.transcribe(file_path, beam_size=5) # get transcription text segments
        
        result = []
        for segment in segments: # list of dictionaries, containing timestamps and text for each segment
            result.append({
                'id'        : segment.id,
                'start_time': segment.start,
                'end_time'  : segment.end,
                'text'      : segment.text
            })
        
        end_time = time.time()
        print("\n\n Time Taken: ", end_time-start_time)
        print("\n\n")
        
        return { # return language, probablity of correct language detection, and the segments
            'language'            : info.language,
            'language_probablity' : info.language_probability,
            'segments'            : result
        }
    except Exception as e:
        return {
            'location': "TRANSCRIPTION",
            'error'   : str(e)
        }