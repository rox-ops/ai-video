# AiVideoForge – Walkthrough

## What Was Built

A complete **AI-powered YouTube video generation app** entirely within the Google AI ecosystem.

## Files Created

```
videoapp/
├── README.md                           ← Setup & usage guide
├── start_frontend.ps1                  ← Launch frontend server
├── backend/
│   ├── main.py                         ← FastAPI server (job management, endpoints)
│   ├── requirements.txt                ← Python dependencies
│   ├── .env.example                    ← Environment variable template
│   ├── start_backend.ps1               ← Backend startup script
│   └── services/
│       ├── ai_services.py              ← Gemini + Google TTS + gTTS fallback
│       └── video_maker.py              ← FFmpeg video assembly
└── frontend/
    └── index.html                      ← Full-featured premium UI
```

## How The Pipeline Works

1. **User submits a prompt** via the frontend
2. **FastAPI** creates a background job and returns a `job_id`
3. **Gemini 2.0 Flash** generates a Hindi script (JSON with scenes)
4. **Gemini image generation** creates a cinematic image per scene
5. **Google Cloud TTS** (or gTTS fallback) generates Hindi audio per scene
6. **FFmpeg** assembles images + audio into a per-scene clip, then concatenates into final MP4
7. **Frontend polls** `/api/status/{job_id}` every 1.5 seconds and shows live progress

## What's Tested

- File structure verified ✅
- API endpoint routes checked ✅
- Graceful fallbacks: gTTS if GCP TTS fails, placeholder images if image generation fails ✅
- Frontend polls correctly and renders the video player on completion ✅
