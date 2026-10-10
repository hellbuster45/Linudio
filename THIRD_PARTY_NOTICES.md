# Third-party software and models

Linudio's own source code is covered by the project's `LICENSE`. It depends on the third-party
software and AI models below, each under its own license. None of the models are included in
this repository: they are downloaded to your machine, into `models/`, the first time you use them.

Licenses were checked against the Hugging Face and GitHub APIs and the installed package
metadata on 2026-10-10. If something here is out of date, the upstream license wins.

## Models used for the translation step: non-commercial only

| Model | License |
| --- | --- |
| `facebook/nllb-200-distilled-600M` (default) | **CC-BY-NC-4.0** |
| `facebook/nllb-200-distilled-1.3B` | **CC-BY-NC-4.0** |
| `facebook/nllb-200-3.3B` | **CC-BY-NC-4.0** |

**CC-BY-NC-4.0 forbids commercial use.** Linudio's code can be used commercially under its own
license, but a Linudio install that translates with an NLLB model cannot. To use Linudio
commercially you would need to swap in a translation model whose license allows it.

## Other models

| Model | Used for | License |
| --- | --- | --- |
| `Systran/faster-whisper-{tiny,small,medium,large-v3}` | Speech-to-text | MIT |
| `mobiuslabsgmbh/faster-whisper-large-v3-turbo` | Speech-to-text | MIT |
| `myshell-ai/MeloTTS-{English,Spanish,French,Chinese,Japanese,Korean}` | Text-to-speech | MIT |
| `google-bert/bert-base-uncased`, `google-bert/bert-base-multilingual-uncased` | MeloTTS text processing | Apache-2.0 |
| `tohoku-nlp/bert-base-japanese-v3` | MeloTTS text processing | Apache-2.0 |
| `dbmdz/bert-base-french-europeana-cased` | MeloTTS text processing | MIT |
| `dccuchile/bert-base-spanish-wwm-uncased` | MeloTTS text processing | No license stated on Hugging Face |
| `kykim/bert-kor-base` | MeloTTS text processing | No license stated on Hugging Face |
| `Kim_Vocal_2.onnx` (vocal separation) | Separating voice from background audio | No license declared by its host repository (`TRvlvr/model_repo`) |

Where no license is stated, check with the publisher before using the model in any context beyond
personal use. These models are fetched on demand and are not redistributed by Linudio.

## Python dependencies

| Package | License |
| --- | --- |
| FastAPI, SQLAlchemy, pydantic-settings, faster-whisper, audio-separator, MeloTTS | MIT |
| uvicorn, PyTorch | BSD-3-Clause |
| transformers, huggingface_hub, python-multipart | Apache-2.0 |
| yt-dlp | Unlicense (public domain) |

Their own dependencies carry further licenses; see each package.

## Frontend dependencies

Next.js, React, HeroUI (`@heroui/react`, `@heroui/styles`), Framer Motion, Radix UI, next-themes,
sonner, clsx, tailwind-merge and tw-animate-css are MIT. lucide-react is ISC.
class-variance-authority is Apache-2.0.

## System tools (not bundled)

- **FFmpeg / FFprobe**: installed separately by you. FFmpeg is LGPL or GPL depending on how your
  build was configured; Linudio only runs it as a separate program.
- **Deno or Node.js**: installed separately; used by yt-dlp to solve YouTube's player challenges.

## Responsible use

Linudio downloads videos from YouTube. Downloading, translating and re-publishing someone else's
video may violate YouTube's Terms of Service and the copyright of the video's owner. Use it only on
content you own or have permission to process.
