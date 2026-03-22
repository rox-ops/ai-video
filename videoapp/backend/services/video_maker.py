"""
video_maker.py - Combines generated images and audio into a final MP4 video using FFmpeg.
"""

import os
import json
import logging
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict

from mutagen import File as MutagenFile
from imageio_ffmpeg import get_ffmpeg_exe

logger = logging.getLogger(__name__)


def _resolve_ffmpeg_bin() -> str:
    """Resolve an ffmpeg binary path from env, PATH, or bundled package."""
    env_bin = os.getenv("FFMPEG_BINARY")
    if env_bin and os.path.exists(env_bin):
        return env_bin

    system_bin = shutil.which("ffmpeg")
    if system_bin:
        return system_bin

    # Bundled static ffmpeg binary from imageio-ffmpeg.
    return get_ffmpeg_exe()


def get_audio_duration(audio_path: str) -> float:
    """Get duration for MP3/WAV audio files without requiring ffprobe."""
    try:
        audio = MutagenFile(audio_path)
        if audio is None or getattr(audio, "info", None) is None:
            raise RuntimeError("Unsupported audio format for duration parsing.")
        return float(audio.info.length)
    except Exception as e:
        logger.warning(f"Could not get audio duration for {audio_path}: {e}. Defaulting to 5s.")
        return 5.0


def create_video_from_scenes(
    scenes: List[Dict],
    output_dir: str,
    job_id: str
) -> str:
    """
    Combines scene images and audio into a final MP4 video.
    
    scenes: list of dicts with keys: scene_number, image_path, audio_path, hindi_text
    output_dir: directory to save output
    job_id: unique job identifier 
    
    Returns: path to the final MP4 file.
    """
    logger.info(f"Starting video assembly for job {job_id} with {len(scenes)} scenes.")
    ffmpeg_bin = _resolve_ffmpeg_bin()
    logger.info(f"Using ffmpeg binary: {ffmpeg_bin}")
    
    # Build individual scene clips  
    clip_paths = []
    
    for scene in scenes:
        scene_num = scene["scene_number"]
        image_path = scene["image_path"]
        audio_path = scene["audio_path"]
        
        if not os.path.exists(image_path) or not os.path.exists(audio_path):
            logger.warning(f"Skipping scene {scene_num}: missing files.")
            continue
        
        duration = get_audio_duration(audio_path)
        clip_path = os.path.join(output_dir, f"clip_{scene_num:02d}.mp4")
        
        # Add a 0.5s buffer to the duration so last audio word isn't cut off
        total_duration = duration + 0.5
        
        command = [
            ffmpeg_bin, "-y",
            "-loop", "1",
            "-i", image_path,
            "-i", audio_path,
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            "-t", str(total_duration),
            "-vf", f"scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1",
            clip_path
        ]
        
        logger.info(f"Rendering scene {scene_num} clip (duration: {total_duration:.2f}s)...")
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"FFmpeg error for scene {scene_num}:\n{result.stderr}")
            raise RuntimeError(f"FFmpeg failed for scene {scene_num}.")
        
        clip_paths.append(clip_path)
        logger.info(f"Scene {scene_num} clip created: {clip_path}")
    
    if not clip_paths:
        raise RuntimeError("No scene clips were created. Cannot assemble video.")
    
    # Create concat list file
    concat_file = os.path.join(output_dir, "concat_list.txt")
    with open(concat_file, "w", encoding="utf-8") as f:
        for clip in clip_paths:
            # Use absolute POSIX paths so ffmpeg concat does not prepend list directory.
            abs_clip = str(Path(clip).resolve()).replace("\\", "/")
            f.write(f"file '{abs_clip}'\n")
    
    # Concatenate all clips into the final video
    final_video_path = os.path.join(output_dir, f"final_video_{job_id}.mp4")
    
    concat_command = [
        ffmpeg_bin, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        final_video_path
    ]
    
    logger.info("Concatenating all scene clips into final video...")
    result = subprocess.run(concat_command, capture_output=True, text=True)
    
    if result.returncode != 0:
        logger.error(f"FFmpeg concat error:\n{result.stderr}")
        raise RuntimeError("FFmpeg failed during final video concatenation.")
    
    logger.info(f"Final video assembled: {final_video_path}")
    
    # Cleanup intermediate clips
    for clip in clip_paths:
        try:
            os.remove(clip)
        except:
            pass
    try:
        os.remove(concat_file)
    except:
        pass
    
    return final_video_path
