"""
ai_services.py - Google AI integrations for AiVideoForge

Uses:
- Google Gemini for script generation
- Placeholder image rendering (with future Gemini image support)
- Google Cloud Text-to-Speech for Hindi narration
"""

import os
import re
import json
import base64
import asyncio
import logging
import wave
from pathlib import Path
from typing import List, Dict, Tuple

import google.generativeai as genai
from google.cloud import texttospeech_v1 as texttospeech
from dotenv import load_dotenv
import requests

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_TEXT_MODEL = os.getenv("GOOGLE_TEXT_MODEL", "models/gemini-2.5-flash")
GOOGLE_IMAGE_MODEL = os.getenv("GOOGLE_IMAGE_MODEL", "models/gemini-2.5-flash-image")
GOOGLE_TTS_MODELS = [
    m.strip() for m in os.getenv(
        "GOOGLE_TTS_MODELS",
        "models/gemini-2.5-flash-preview-tts,models/gemini-2.5-pro-preview-tts"
    ).split(",") if m.strip()
]
GOOGLE_TTS_VOICE = os.getenv("GOOGLE_TTS_VOICE", "Kore")
genai.configure(api_key=GOOGLE_API_KEY)


def _gemini_generate_content_raw(model_name: str, body: Dict) -> Dict:
    """Call Gemini generateContent over REST and return raw JSON."""
    if not GOOGLE_API_KEY:
        raise RuntimeError("GOOGLE_API_KEY is not configured.")

    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={GOOGLE_API_KEY}"
    response = requests.post(url, json=body, timeout=120)
    response.raise_for_status()
    return response.json()


def _save_gemini_audio_bytes(audio_bytes: bytes, mime_type: str, scene_number: int, output_dir: str) -> str:
    """Persist Gemini TTS audio bytes, converting PCM L16 payloads into WAV files."""
    mime = (mime_type or "").lower()

    # Gemini preview TTS commonly returns raw PCM as audio/L16;codec=pcm;rate=24000
    if "audio/l16" in mime or "codec=pcm" in mime:
        rate_match = re.search(r"rate=(\d+)", mime)
        sample_rate = int(rate_match.group(1)) if rate_match else 24000
        audio_path = os.path.join(output_dir, f"audio_{scene_number:02d}.wav")
        with wave.open(audio_path, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # 16-bit PCM
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_bytes)
        return audio_path

    if "audio/mpeg" in mime or "audio/mp3" in mime:
        audio_path = os.path.join(output_dir, f"audio_{scene_number:02d}.mp3")
    else:
        # Safe default for most non-MP3 responses.
        audio_path = os.path.join(output_dir, f"audio_{scene_number:02d}.wav")

    with open(audio_path, "wb") as f:
        f.write(audio_bytes)
    return audio_path


def generate_hindi_script(prompt: str) -> Dict:
    """
    Uses Gemini to generate a Hindi narration script with scene breakdowns.
    Returns a dict with 'title', 'scenes' (list of {scene_number, hindi_text, image_prompt}).
    """
    logger.info(f"Generating Hindi script for prompt: {prompt}")

    model = genai.GenerativeModel(
        model_name=GOOGLE_TEXT_MODEL,
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
        body = {
            "contents": [{"parts": [{"text": enhanced_prompt}]}],
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"]
            }
        }
        data = _gemini_generate_content_raw(GOOGLE_IMAGE_MODEL, body)

        candidates = data.get("candidates", [])
        for cand in candidates:
            parts = cand.get("content", {}).get("parts", [])
            for part in parts:
                inline = part.get("inlineData")
                if not inline:
                    continue
                mime = inline.get("mimeType", "")
                payload = inline.get("data", "")
                if mime.startswith("image/") and payload:
                    image_bytes = base64.b64decode(payload)
                    ext = ".png" if "png" in mime else ".jpg"
                    image_path = os.path.join(output_dir, f"scene_{scene_number:02d}{ext}")
                    with open(image_path, "wb") as f:
                        f.write(image_bytes)
                    logger.info(f"Gemini image saved: {image_path}")
                    return image_path

        raise RuntimeError("Gemini image response did not include image data.")

    except Exception as e:
        logger.warning(f"Gemini image generation failed for scene {scene_number}: {e}")
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
    Uses Gemini TTS models first to generate Hindi narration.
    Falls back to Google Cloud TTS and then gTTS.
    Returns path to the saved audio file.
    """
    logger.info(f"Generating Hindi audio for scene {scene_number}")

    try:
        return _gemini_tts(text, scene_number, output_dir)
    except Exception as e:
        logger.warning(f"Gemini TTS failed: {e}. Trying Google Cloud TTS fallback...")

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


def _gemini_tts(text: str, scene_number: int, output_dir: str) -> str:
    """Generate Hindi speech audio using Gemini TTS models."""
    tts_prompt = (
        "Speak the following text naturally in Hindi (hi-IN). "
        "Keep pronunciation clear and expressive.\n\n"
        f"Text: {text}"
    )

    last_error = None
    for model_name in GOOGLE_TTS_MODELS:
        try:
            body = {
                "contents": [{"parts": [{"text": tts_prompt}]}],
                "generationConfig": {
                    "responseModalities": ["AUDIO"],
                    "speechConfig": {
                        "voiceConfig": {
                            "prebuiltVoiceConfig": {
                                "voiceName": GOOGLE_TTS_VOICE
                            }
                        }
                    }
                }
            }
            data = _gemini_generate_content_raw(model_name, body)
            candidates = data.get("candidates", [])

            for cand in candidates:
                parts = cand.get("content", {}).get("parts", [])
                for part in parts:
                    inline = part.get("inlineData")
                    if not inline:
                        continue
                    mime = inline.get("mimeType", "")
                    payload = inline.get("data", "")
                    if mime.startswith("audio/") and payload:
                        audio_bytes = base64.b64decode(payload)
                        audio_path = _save_gemini_audio_bytes(
                            audio_bytes=audio_bytes,
                            mime_type=mime,
                            scene_number=scene_number,
                            output_dir=output_dir,
                        )
                        logger.info(f"Gemini TTS audio saved ({model_name}): {audio_path}")
                        return audio_path

            raise RuntimeError(f"No audio data found in Gemini response for {model_name}.")

        except Exception as e:
            last_error = e
            logger.warning(f"Gemini TTS model failed ({model_name}): {e}")

    raise RuntimeError(f"All Gemini TTS models failed. Last error: {last_error}")


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
