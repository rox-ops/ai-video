# 🎬 AiVideoForge – AI YouTube Video Generator

Generate complete Hindi YouTube videos from any text prompt using **Google AI** (Gemini) and Google Cloud Text-to-Speech.

## ✨ What It Does

1. **Enter a prompt** (in Hindi or English)
2. **Gemini AI** generates a Hindi script with scene breakdowns
3. **Gemini** creates cinematic images for each scene
4. **Google Cloud TTS** generates natural Hindi narration
5. **FFmpeg** assembles everything into a YouTube-ready `.mp4`

---

## 🛠️ Setup

### Prerequisites
- ✅ Python 3.9+
- ✅ [FFmpeg](https://ffmpeg.org/download.html) installed and on your `PATH`
- ✅ A [Google AI API Key](https://aistudio.google.com/app/apikey) (free tier available)
- ✅ *(Optional)* A Google Cloud project with [Text-to-Speech API](https://cloud.google.com/text-to-speech) enabled for better voice quality

### 1. Get Your API Key
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key (free)
3. Copy it

### 2. Configure Environment
```bash
cd backend
copy .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

Your `.env` should look like:
```
GOOGLE_API_KEY=AIza...your_key_here
```

### 3. Install FFmpeg (Windows)
Download from [ffmpeg.org](https://ffmpeg.org/download.html) → Windows builds → and add the `bin/` folder to your Windows PATH.

Or install via winget:
```powershell
winget install ffmpeg
```

---

## 🚀 Running the App

### Start Backend (Terminal 1)
```powershell
cd backend
.\start_backend.ps1
```
The API will be available at `http://localhost:8000`

### Start Frontend (Terminal 2)
```powershell
# From the videoapp root folder:
.\start_frontend.ps1
```
Then open **http://localhost:3000** in your browser.

Or just open `frontend/index.html` directly in your browser.

---

## 📁 Project Structure
```
videoapp/
├── backend/
│   ├── main.py               # FastAPI server & job management
│   ├── requirements.txt      # Python dependencies
│   ├── .env.example          # Environment variable template
│   ├── start_backend.ps1     # Windows startup script
│   └── services/
│       ├── ai_services.py    # Gemini + Google TTS integrations
│       └── video_maker.py    # FFmpeg video assembly
├── frontend/
│   └── index.html            # Full-featured frontend UI
└── start_frontend.ps1        # Frontend startup script
```

---

## 🔑 API Keys & Services

| Service | Purpose | Cost |
|---|---|---|
| [Google AI (Gemini)](https://aistudio.google.com) | Script + Image generation | Free tier available |
| [Google Cloud TTS](https://cloud.google.com/text-to-speech) | Hindi voice (WaveNet) | 1M chars/month free |
| gTTS (fallback) | Hindi voice backup | Completely free |
| FFmpeg | Video rendering | Free & open source |

### TTS Setup (for better voice quality)
If you want WaveNet quality voices:
1. Create a project on [Google Cloud Console](https://console.cloud.google.com)
2. Enable "Cloud Text-to-Speech API"
3. Create a Service Account and download the JSON key
4. Set `GOOGLE_APPLICATION_CREDENTIALS=path/to/key.json` in your `.env`

**If you skip this, the app automatically falls back to gTTS (free, works without Cloud account).**

---

## 🌐 API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/generate` | POST | Start video generation job |
| `/api/status/{job_id}` | GET | Poll job progress |
| `/api/health` | GET | Health check |
| `/videos/{path}` | GET | Download generated video |

---

## ⚙️ Troubleshooting

**❌ `ffmpeg not found`**
→ Install FFmpeg and add it to PATH. Restart your terminal.

**❌ `Could not connect to backend`**
→ Make sure the backend is running with `start_backend.ps1`

**❌ `Invalid API key`**
→ Double-check your `.env` file has the correct `GOOGLE_API_KEY`

**❌ Image generation fails**
→ The app will use styled placeholder images automatically. Full image generation requires access to `gemini-2.0-flash-preview-image-generation` model.
