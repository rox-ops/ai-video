# AiVideoForge Implementation Plan

## Goal Description
Build a web application that takes a user prompt and generates a complete YouTube video in Hindi. The process involves generating a Hindi script, creating relevant images, producing Hindi voice narration, and combining them into an MP4 video using the Google AI ecosystem. 

## User Review Required
> [!IMPORTANT]
> - Do you want to proceed with the Next.js (frontend) + FastAPI/Python (backend) technical stack?
> - For video assembly, the backend will require `ffmpeg` installed on the system.
> - Google Generative AI API keys will be required for script, image, and (if supported natively) audio generation. Alternatively, we can use Google Cloud Text-to-Speech for the Hindi narration if Gemini Audio isn't fully available yet. Which would you prefer?

## Proposed Changes

### Backend (Python/FastAPI)
- `backend/main.py`: Main FastAPI application exposing the `/generate_video` endpoint.
- `backend/ai_services.py`: Integration with Google Gemini for:
  - Script generation (Prompt -> Hindi Script with scene breakdowns).
  - Image generation (Scene context -> Image generation using Gemini).
  - Audio generation (Text -> Hindi Speech).
- `backend/video_maker.py`: Uses `ffmpeg-python` to stitch the generated images and audio together into a final `.mp4` file.

### Frontend (Next.js)
- `frontend/`: A modern Next.js React application with:
  - An input form to accept user prompts.
  - A beautiful, modern, dark-mode aesthetic.
  - A loading skeleton and progress indicator (script generation -> images -> audio -> rendering).
  - A final video player displaying the result and a download link.

## Verification Plan
### Automated Tests
- N/A for initial prototype unless requested.

### Manual Verification
- Start backend and frontend servers.
- Submit a prompt "A story about a brave tiger in the jungle".
- Monitor the backend logs to ensure Google APIs are successfully called.
- Verify that a final `.mp4` file is generated and successfully plays on the frontend with the correct images and Hindi narration.
