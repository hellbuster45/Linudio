# Linudio

### AI-Powered YouTube Video Translation & Dubbing

Linudio is a full-stack application for translating and dubbing YouTube videos into other languages using locally hosted AI models.

The application takes a YouTube video, extracts its audio, generates a timestamped transcript using **Whisper**, translates the transcript using **NLLB-200**, generates translated speech using **MeloTTS**, synchronizes the generated speech with the original timestamps, mixes it with the video's background audio, and produces a dubbed version of the original video.

> **Note:** Linudio is currently a development/academic project. Some parts of the audio-separation pipeline are still under development and the current implementation has specific environment and storage assumptions.

---

## Features

- YouTube video ingestion using `yt-dlp`
- Automatic video metadata extraction
- Audio extraction and preprocessing with FFmpeg
- Speech-to-text transcription using **Faster-Whisper**
- Automatic source-language detection
- Timestamp-preserving transcripts
- Multilingual translation using **NLLB-200**
- Editable original and translated transcript segments
- Local text-to-speech generation using **MeloTTS**
- Per-segment speech generation
- Automatic TTS duration synchronization
- Timestamp-aligned voice assembly
- Background music / audio mixing
- Final audio-video muxing with FFmpeg
- Background processing for long-running dubbing jobs
- Dubbing status polling
- REST API built with FastAPI
- PostgreSQL support through SQLAlchemy
- Modern Next.js frontend

---

## Architecture

```text
                         ┌─────────────────────┐
                         │     Next.js UI      │
                         │      :3000          │
                         └──────────┬──────────┘
                                    │
                                    │ REST API
                                    ▼
                         ┌─────────────────────┐
                         │      FastAPI        │
                         │       :8000         │
                         └──────────┬──────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
       ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
       │ Video Module │      │  STT Module   │      │ Translation  │
       │              │      │              │      │    Module    │
       │   yt-dlp     │      │ Whisper      │      │    NLLB      │
       │   FFmpeg     │      │              │      │              │
       └──────┬───────┘      └──────┬───────┘      └──────┬───────┘
              │                     │                     │
              └─────────────────────┼─────────────────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │     TTS Module      │
                         │                     │
                         │      MeloTTS        │
                         │      FFmpeg          │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    Dubbed Video     │
                         │       .mp4          │
                         └─────────────────────┘
```

---

## Processing Pipeline

### 1. YouTube Video

The user provides a YouTube URL.

Linudio extracts metadata such as:

- Video ID
- Title
- Thumbnail
- Duration
- Upload date
- Resolution
- FPS

The video is then downloaded into local storage using `yt-dlp`.

```text
YouTube URL
     │
     ▼
Metadata Extraction
     │
     ▼
Video Download
     │
     ▼
FFmpeg Audio Extraction
     ├── Stereo WAV
     └── Mono 16 kHz WAV
```

---

### 2. Speech-to-Text

The mono audio track is processed using:

**Faster-Whisper — `large-v3-turbo`**

The transcription pipeline generates timestamped segments:

```json
{
  "id": 1,
  "start_time": 0.0,
  "end_time": 6.0,
  "text": "Welcome to English in a Minute."
}
```

Whisper also detects the source language and provides a language probability.

---

### 3. Translation

The transcript is translated using:

**Facebook NLLB-200 Distilled 600M**

The model runs locally through Hugging Face Transformers and PyTorch.

Translation preserves the original segment structure:

```text
Original Segment
       │
       ├── Start time
       ├── End time
       └── Text
              │
              ▼
         NLLB-200
              │
              ▼
Translated Segment
       │
       ├── Start time
       ├── End time
       └── Translated text
```

The frontend allows the user to edit both the original transcript and translated segments before starting the dubbing process.

---

### 4. Text-to-Speech

The translated segments are converted to speech using **MeloTTS**.

Instead of generating one long audio file, Linudio generates one WAV file per transcript segment:

```text
temp_dubs/
├── seg_1.wav
├── seg_2.wav
├── seg_3.wav
└── ...
```

This makes it possible to align each generated speech segment with its original timestamp.

---

### 5. Duration Synchronization

Generated speech does not necessarily have the same duration as the original transcript segment.

Linudio measures the generated audio duration and uses FFmpeg's `atempo` filter when adjustment is required.

For example:

```text
Original segment:
00:10 → 00:15
Duration: 5 seconds

Generated speech:
Duration: 6.2 seconds

             │
             ▼
        FFmpeg atempo
             │
             ▼
      ~5 second audio
```

This helps keep the dubbed speech synchronized with the original video timeline.

---

### 6. Audio Assembly

The individual speech segments are positioned using their original timestamps.

Conceptually:

```text
Timeline
─────────────────────────────────────────────>

Segment 1
████████

              Segment 2
              ███████████

                            Segment 3
                            ███████
```

FFmpeg is then used to:

1. Align the generated speech segments.
2. Merge them into a single vocal track.
3. Mix the generated voice with background audio.
4. Replace the original video's audio.
5. Preserve the original video stream.

The final output is:

```text
<video_id>_dubbed.mp4
```

---

# Tech Stack

## Frontend

- Next.js 16
- React 19
- TypeScript
- HeroUI
- Tailwind CSS
- Framer Motion
- Lucide React

## Backend

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic Settings
- Uvicorn

## AI / ML

- Faster-Whisper
- Whisper `large-v3-turbo`
- Facebook NLLB-200 Distilled 600M
- MeloTTS
- PyTorch
- Hugging Face Transformers

## Media Processing

- FFmpeg
- FFprobe
- yt-dlp

---

# Project Structure

```text
Audio-Processor/
│
├── backend/
│   │
│   ├── api/
│   │   └── v1/
│   │       │
│   │       ├── stt/
│   │       │   ├── models.py
│   │       │   ├── routes.py
│   │       │   ├── schemas.py
│   │       │   └── services.py
│   │       │
│   │       ├── text_translation/
│   │       │   ├── models.py
│   │       │   ├── routes.py
│   │       │   ├── schemas.py
│   │       │   └── services.py
│   │       │
│   │       ├── tts/
│   │       │   ├── models.py
│   │       │   ├── routes.py
│   │       │   ├── schemas.py
│   │       │   ├── services.py
│   │       │   └── tts_worker.py
│   │       │
│   │       ├── videos/
│   │       │   ├── models.py
│   │       │   ├── routes.py
│   │       │   ├── schemas.py
│   │       │   └── services.py
│   │       │
│   │       └── helpers.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   └── utils.py
│   │
│   ├── database.py
│   ├── main.py
│   ├── requirements.txt
│   └── API_structure.md
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx
│   │   ├── layout.tsx
│   │   └── globals.css
│   │
│   ├── components/
│   │   ├── FetchVideo.tsx
│   │   ├── TranscriptField.tsx
│   │   ├── TranscriptPane.tsx
│   │   ├── TranslatedPane.tsx
│   │   └── VideoCard.tsx
│   │
│   ├── lib/
│   │   ├── constants.ts
│   │   └── utils.ts
│   │
│   ├── package.json
│   └── next.config.ts
│
└── README.md
```

---

# Requirements

Before running Linudio, install the following:

### Required

- Python 3.10+
- Node.js
- FFmpeg
- FFprobe
- PostgreSQL
- Git

The backend uses several ML models that require significant CPU memory and disk space.

A GPU is not currently required by the implementation; the Whisper and translation models are configured to run on CPU.

---

# Backend Setup

Clone the repository:

```bash
git clone https://github.com/hellbuster45/Audio-Processor.git
cd Audio-Processor
```

Create and activate a Python virtual environment:

### Windows

```bash
cd backend

python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
cd backend

python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# FFmpeg Setup

FFmpeg and FFprobe must be installed separately from Python dependencies.

Verify the installation:

```bash
ffmpeg -version
ffprobe -version
```

Both commands should be available from your system `PATH`.

---

# Environment Variables

Create a `.env` file inside `backend/`:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/linudio
SECRET_KEY=your-secret-key
ALGORITHM=HS256
```

The backend reads these values through `pydantic-settings`.

---

# Database

Create a PostgreSQL database:

```sql
CREATE DATABASE linudio;
```

Update `DATABASE_URL` in `.env` to point to the database.

The backend uses SQLAlchemy for database access.

The current database models store information including:

- Downloaded videos
- Video metadata
- Transcript data
- Translated transcript data
- Dubbing job status

---

# Running the Backend

From the `backend` directory:

```bash
uvicorn main:app --reload
```

The API will be available at:

```text
http://localhost:8000
```

FastAPI's interactive API documentation is available at:

```text
http://localhost:8000/docs
```

---

# Frontend Setup

Open another terminal:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Run the development server:

```bash
npm run dev
```

The frontend will be available at:

```text
http://localhost:3000
```

---

# API

## Health Check

```http
GET /
```

Response:

```json
{
  "status": "app running yay! :D"
}
```

---

## Fetch YouTube Video

```http
POST /videos/yt_video
```

Request:

```json
{
  "url": "https://www.youtube.com/watch?v=v4t0E3S1N1k"
}
```

The API immediately returns video metadata while the actual download is performed as a background task.

Example response:

```json
{
  "message": "Download Started..",
  "metadata": {
    "video_id": "v4t0E3S1N1k",
    "title": "English in a Minute: Grow Like a Weed",
    "thumbnail": "https://i.ytimg.com/vi/v4t0E3S1N1k/maxresdefault.jpg",
    "duration": 60,
    "upload_date": "20230619",
    "resolution": "1920x1080",
    "fps": 30
  }
}
```

---

## Generate Transcript

```http
POST /synthesize/
```

Request:

```json
{
  "video_id": "v4t0E3S1N1k"
}
```

Example response:

```json
{
  "src_lang": "eng_Latn",
  "language_probability": 0.9998,
  "segments": [
    {
      "id": 1,
      "start_time": 0.0,
      "end_time": 6.0,
      "text": "Welcome to English in a Minute."
    }
  ]
}
```

---

## Translate Transcript

```http
POST /translate/
```

Request:

```json
{
  "video_id": "v4t0E3S1N1k",
  "tgt_lang": "jpn_Jpan",
  "segments": [
    {
      "id": 1,
      "start_time": 0.0,
      "end_time": 6.0,
      "text": "Welcome to English in a Minute."
    }
  ]
}
```

Example response:

```json
{
  "status": "success",
  "tgt_lang": "jpn_Jpan",
  "translated_segments": [
    {
      "id": 1,
      "start_time": 0.0,
      "end_time": 6.0,
      "text": "英語にようこそ!"
    }
  ]
}
```

---

## Start Dubbing

```http
POST /text_to_speech/dub
```

Request:

```json
{
  "video_id": "v4t0E3S1N1k",
  "lang_code": "jpn_Jpan",
  "segments": [
    {
      "id": 1,
      "start_time": 0.0,
      "end_time": 6.0,
      "text": "英語にようこそ!"
    }
  ]
}
```

The dubbing pipeline runs as a background task.

Response:

```json
{
  "status": "started",
  "video_id": "v4t0E3S1N1k"
}
```

---

## Check Dubbing Status

```http
GET /text_to_speech/dub_status?video_id=<VIDEO_ID>
```

While processing:

```json
{
  "status": "tts_generation"
}
```

When complete:

```json
{
  "status": "success",
  "video_path": "http://localhost:8000/storage/<VIDEO_ID>/<VIDEO_ID>_dubbed.mp4"
}
```

---

# Supported Translation Languages

The frontend/backend currently includes mappings for languages such as:

- English
- Hindi
- Spanish
- French
- German
- Japanese
- Korean
- Chinese
- Russian
- Bengali
- Marathi
- Telugu
- Tamil
- Gujarati
- Urdu
- Kannada
- Malayalam
- Punjabi
- Italian
- Portuguese
- Vietnamese
- Indonesian
- Thai
- Turkish

Actual TTS availability is more limited than the complete NLLB language mapping because MeloTTS uses its own supported language set.

---

# Local Storage

Downloaded and generated media is stored under:

```text
backend/storage/videos/
```

A typical video directory looks like:

```text
storage/
└── videos/
    └── <video_id>/
        ├── <video_id>_video.mp4
        ├── <video_id>_stereo.wav
        ├── <video_id>_mono.wav
        ├── temp_dubs/
        │   ├── batch_segments.json
        │   ├── seg_1.wav
        │   ├── seg_2.wav
        │   └── ...
        ├── translated_vocals.wav
        ├── final_mix.wav
        └── <video_id>_dubbed.mp4
```

---

# Design Decisions

### Timestamp-based dubbing

Rather than concatenating translated speech sequentially, Linudio retains the original transcript timestamps.

This allows generated speech to be positioned at approximately the same point in the source video.

### Local AI inference

The primary AI components run locally:

```text
YouTube
   ↓
Faster-Whisper
   ↓
NLLB-200
   ↓
MeloTTS
   ↓
FFmpeg
```

No external paid speech-to-text, translation, or text-to-speech API is required by the current implementation.

### Background processing

Video downloading and dubbing can take considerably longer than a normal HTTP request.

FastAPI background tasks are therefore used for these operations, while the frontend periodically checks the dubbing status.

---

# Current Limitations

Linudio is still under active development.

### Audio separation

The repository contains an implementation for vocal/background separation using `audio-separator` and `Kim_Vocal_2.onnx`, but the separation call is currently disabled in the active dubbing pipeline.

The current dubbing code expects a previously generated background track at the configured storage location.

### CPU inference

Whisper, NLLB and MeloTTS are currently configured for CPU execution.

Processing long videos can therefore be computationally expensive and slow.

### TTS language coverage

NLLB supports substantially more languages than the current MeloTTS integration. Consequently, a language being available for translation does not necessarily mean that it can be synthesized by the current TTS pipeline.

### YouTube availability

Video downloading depends on `yt-dlp` and YouTube's current delivery/access mechanisms. Some videos may require cookies or may not be downloadable.

### Development storage

Media is currently stored on the local filesystem rather than object storage such as S3.

### Background jobs

The current implementation uses FastAPI background tasks rather than a dedicated distributed job queue such as Celery, RQ, or a message broker.

---

# Future Improvements

Potential improvements include:

- [ ] Fully integrate automatic vocal/background separation
- [ ] GPU acceleration for Whisper, NLLB and TTS
- [ ] Better speaker-aware TTS
- [ ] Voice cloning / voice preservation
- [ ] Dedicated job queue for long-running processing
- [ ] WebSocket-based processing progress
- [ ] Improved audio alignment
- [ ] Automatic silence and pause preservation
- [ ] Better handling of long videos
- [ ] Cloud/object storage support
- [ ] Authentication and authorization
- [ ] Rate limiting
- [ ] Docker-based deployment
- [ ] Production deployment configuration
- [ ] More TTS language support
- [ ] Automatic subtitle generation/export
- [ ] Multiple speaker detection and voice assignment

---

# Development

Run the backend:

```bash
cd backend
uvicorn main:app --reload
```

Run the frontend:

```bash
cd frontend
npm run dev
```

Then open:

```text
http://localhost:3000
```

---

# License

This project currently does not specify a license.

If you intend to make the repository open source, add an appropriate `LICENSE` file before publishing or redistributing the project.

---

## Acknowledgements

Linudio is built on top of several open-source projects and models, including:

- Faster-Whisper
- Whisper
- Hugging Face Transformers
- NLLB-200
- MeloTTS
- PyTorch
- FFmpeg
- yt-dlp
- FastAPI
- Next.js
- SQLAlchemy
