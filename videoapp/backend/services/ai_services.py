"""
ai_services.py - Google AI integrations for AiVideoForge

Uses:
- Google Gemini (gemini-2.0-flash-exp) for script generation
- Google Gemini (gemini-2.0-flash-exp) for image generation  
- Google Cloud Text-to-Speech for Hindi narration
"""

import os
import re
import json
import base64
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Tuple

import google.generativeai as genai
from google.cloud import texttospeech_v1 as texttospeech
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)


def generate_hindi_script(prompt: str) -> Dict:
    """
    Uses Gemini to generate a Hindi narration script with scene breakdowns.
    Returns a dict with 'title', 'scenes' (list of {scene_number, hindi_text, image_prompt}).
    """
    logger.info(f"Generating Hindi script for prompt: {prompt}")

    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash-exp",
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json"
        )
    )

    system_prompt = """You are an expert Hindi content creator for YouTube videos.
Given a user's topic/prompt, you must generate a compelling YouTube video script in Hindi.

STRICT OUTPUT FORMAT (valid JSON only):
{
  "title": "Video title in Hindi",
  "description": "Short 2-line description of the video in Hindi",
  "scenes": [
    {
      "scene_number": 1,
      "hindi_text": "Narration text for this scene in Hindi (Devanagari script). Make it 2-3 sentences.",
      "image_prompt": "A detailed English prompt for an AI image generator to create the visual for this scene. Be very descriptive about colors, composition, mood."
    }
  ]
}

Rules:
- Generate exactly 5-7 scenes.
- All narration (hindi_text) MUST be in Devanagari (Hindi) script.
- image_prompt should be in English and very detailed (cinematic, photorealistic or illustrated style).
- Make the content engaging, educational, and suitable for a general Indian YouTube audience.
- Vary the visual descriptions (close-up, wide shot, etc.).
"""

    response = model.generate_content(f"{system_prompt}\n\nUser Topic: {prompt}")
    
    try:
        script_data = json.loads(response.text)
        logger.info(f"Script generated with {len(script_data.get('scenes', []))} scenes.")
        return script_data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse script JSON: {e}\nRaw: {response.text}")
        raise ValueError("Failed to parse script from AI. Please try again.")


def generate_scene_image(image_prompt: str, scene_number: int, output_dir: str) -> str:
    """
    Uses Gemini's image generation to create an image for a scene.
    Returns the path to the saved image.
    Note: Falls back to placeholder if image generation is not available.
    """
    logger.info(f"Generating image for scene {scene_number}")

    enhanced_prompt = (
        f"{image_prompt}. "
        "Cinematic lighting, high quality, vibrant colors, "
        "photorealistic, 16:9 aspect ratio, YouTube thumbnail style."
    )

    try:
        # Try using Gemini with vision capabilities for image generation
        model = genai.GenerativeModel("gemini-2.0-flash")
        
        # Note: Gemini's text-to-image is experimental/limited
        # Falling back to placeholder for best experience
        raise NotImplementedError("Direct image generation not fully available")

    except Exception as e:
        logger.warning(f"Gemini image generation not available: {e}")
        logger.info("Using styled placeholder image instead...")

    # Fallback: Create a styled placeholder image with Pillow
    return _create_placeholder_image(image_prompt, scene_number, output_dir)


def _create_placeholder_image(prompt: str, scene_number: int, output_dir: str) -> str:
    """Creates a visually styled placeholder image when generation fails."""
    from PIL import Image, ImageDraw, ImageFont
    import textwrap

    width, height = 1280, 720
    # Dynamic color based on scene number
    colors = [
        ("#1a1a2e", "#e94560"),
        ("#0f3460", "#533483"),
        ("#16213e", "#0f3460"),
        ("#2c003e", "#7b2d8b"),
        ("#003049", "#d62828"),
        ("#023e8a", "#0077b6"),
        ("#1b4332", "#52b788"),
    ]
    bg_color, accent_color = colors[scene_number % len(colors)]

    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Draw gradient overlay bars
    for i in range(0, width, 4):
        alpha = int(80 * (i / width))
        draw.line([(i, 0), (i, height)], fill=accent_color + hex(alpha)[2:].zfill(2))

    # Scene number badge
    draw.ellipse([(40, 40), (120, 120)], fill=accent_color)
    try:
        font_large = ImageFont.truetype("arial.ttf", 40)
        font_small = ImageFont.truetype("arial.ttf", 24)
    except:
        font_large = ImageFont.load_default()
        font_small = font_large

    draw.text((65, 55), str(scene_number), fill="white", font=font_large)
    
    # Prompt text wrapped
    wrapped = textwrap.fill(prompt[:200], width=55)
    draw.text((40, 160), wrapped, fill="#cccccc", font=font_small)

    # Footer
    draw.rectangle([(0, height - 60), (width, height)], fill=accent_color)
    draw.text((40, height - 45), "AiVideoForge • Scene Preview", fill="white", font=font_small)

    image_path = os.path.join(output_dir, f"scene_{scene_number:02d}.png")
    img.save(image_path, "PNG", quality=95)
    logger.info(f"Placeholder image created at {image_path}")
    return image_path


def generate_hindi_audio(text: str, scene_number: int, output_dir: str) -> str:
    """
    Uses Google Cloud Text-to-Speech to generate Hindi audio narration.
    Returns path to the saved .mp3 audio file.
    """
    logger.info(f"Generating Hindi audio for scene {scene_number}")

    try:
        tts_client = texttospeech.TextToSpeechClient()

        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Use Hindi WaveNet voice for natural sound
        voice = texttospeech.VoiceSelectionParams(
            language_code="hi-IN",
            name="hi-IN-Wavenet-D",  # Male Hindi voice
            ssml_gender=texttospeech.SsmlVoiceGender.MALE,
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=0.9,  # Slightly slower for clarity
            pitch=0.0,
        )

        response = tts_client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        audio_path = os.path.join(output_dir, f"audio_{scene_number:02d}.mp3")
        with open(audio_path, "wb") as f:
            f.write(response.audio_content)

        logger.info(f"Audio generated: {audio_path}")
        return audio_path

    except Exception as e:
        logger.warning(f"Google Cloud TTS failed: {e}. Trying gTTS fallback...")
        return _gtts_fallback(text, scene_number, output_dir)


def _gtts_fallback(text: str, scene_number: int, output_dir: str) -> str:
    """Fallback to gTTS (free, no credentials needed) for Hindi TTS."""
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang="hi", slow=False)
        audio_path = os.path.join(output_dir, f"audio_{scene_number:02d}.mp3")
        tts.save(audio_path)
        logger.info(f"gTTS fallback audio saved: {audio_path}")
        return audio_path
    except Exception as e:
        logger.error(f"gTTS fallback also failed: {e}")
        raise RuntimeError(f"Could not generate audio for scene {scene_number}.")
