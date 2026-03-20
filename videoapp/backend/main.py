"""
main.py - FastAPI server for AiVideoForge
Handles video generation jobs, serves generated videos, and streams progress.
"""

import os
import uuid
import json
import asyncio
import logging
import threading
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AiVideoForge API", version="1.0.0")

# Allow frontend to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory for generated assets
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "generated_videos")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Mount static files for video download
app.mount("/videos", StaticFiles(directory=OUTPUT_DIR), name="videos")

# In-memory job registry
# In production, replace with Redis or a database
jobs: Dict[str, Dict[str, Any]] = {}


class VideoRequest(BaseModel):
    prompt: str


def _update_job(job_id: str, **kwargs):
    """Helper to update job state."""
    if job_id in jobs:
        jobs[job_id].update(kwargs)


def _run_generation_pipeline(job_id: str, prompt: str):
    """
    Background thread that runs the full video generation pipeline.
    Updates job status at each stage so the frontend can show progress.
    """
    from services.ai_services import generate_hindi_script, generate_scene_image, generate_hindi_audio
    from services.video_maker import create_video_from_scenes

    job_dir = os.path.join(OUTPUT_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    try:
        # --- Stage 1: Generate Hindi Script ---
        _update_job(job_id, status="generating_script", progress=5,
                    message="✍️ Gemini AI is writing your Hindi script...")
        script_data = generate_hindi_script(prompt)
        _update_job(job_id, status="script_done", progress=20,
                    message=f"📝 Script ready! '{script_data.get('title', '')}' ({len(script_data['scenes'])} scenes)",
                    script=script_data)

        assembled_scenes = []
        total_scenes = len(script_data["scenes"])

        # --- Stage 2: Generate Images & Audio in parallel per scene ---
        for i, scene in enumerate(script_data["scenes"]):
            scene_num = scene["scene_number"]
            base_progress = 20 + int((i / total_scenes) * 55)

            _update_job(job_id, progress=base_progress,
                        message=f"🎨 Creating image for scene {scene_num}/{total_scenes}...")
            image_path = generate_scene_image(scene["image_prompt"], scene_num, job_dir)

            _update_job(job_id, progress=base_progress + 5,
                        message=f"🎙️ Generating Hindi voice for scene {scene_num}/{total_scenes}...")
            audio_path = generate_hindi_audio(scene["hindi_text"], scene_num, job_dir)

            assembled_scenes.append({
                "scene_number": scene_num,
                "hindi_text": scene["hindi_text"],
                "image_path": image_path,
                "audio_path": audio_path,
            })

        # --- Stage 3: Render final video ---
        _update_job(job_id, status="rendering_video", progress=80,
                    message="🎬 Rendering final video with FFmpeg...")
        final_video = create_video_from_scenes(assembled_scenes, job_dir, job_id)

        # Get relative path for URL
        rel_path = os.path.relpath(final_video, OUTPUT_DIR).replace("\\", "/")
        video_url = f"/videos/{rel_path}"

        _update_job(
            job_id,
            status="completed",
            progress=100,
            message="✅ Video ready! Enjoy your content.",
            video_url=video_url,
        )
        logger.info(f"Job {job_id} completed. Video: {final_video}")

    except Exception as e:
        logger.exception(f"Job {job_id} failed: {e}")
        _update_job(job_id, status="failed", progress=0, message=f"❌ Error: {str(e)}")


@app.post("/api/generate")
async def generate_video(request: VideoRequest):
    """Start a video generation job. Returns a job_id to poll for status."""
    prompt = request.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")
    if len(prompt) > 1000:
        raise HTTPException(status_code=400, detail="Prompt too long. Max 1000 characters.")

    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "job_id": job_id,
        "prompt": prompt,
        "status": "queued",
        "progress": 0,
        "message": "⏳ Job queued...",
        "script": None,
        "video_url": None,
    }

    # Run the pipeline in a background thread (non-blocking)
    thread = threading.Thread(target=_run_generation_pipeline, args=(job_id, prompt), daemon=True)
    thread.start()

    logger.info(f"Started job {job_id} for prompt: '{prompt[:50]}...'")
    return {"job_id": job_id, "status": "queued"}


@app.get("/api/status/{job_id}")
async def get_job_status(job_id: str):
    """Poll this endpoint to get the current status of a video generation job."""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "AiVideoForge API"}
