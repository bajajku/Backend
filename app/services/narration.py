"""Narration generation and TTS synthesis service."""

import httpx
import structlog

from app.config import Settings
from app.models.analysis import ContentAnalysis
from app.models.schemas import MatchedModel
from app.utils.gcs import GCSClient
from app.utils.llm import LLM

logger = structlog.get_logger()

NARRATION_PROMPT = """Write a 2-3 sentence explanation for a 3D model in an educational scene.

Context: The user uploaded a document about "{topic}".
Model: {model_name} - {model_description}

Requirements:
- Start with "This {model_name} represents..."
- Directly connect the model to concepts from the document
- Tone: friendly, clear, accessible (suitable for users with ADHD/dyslexia)
- Keep under 50 words
- Do not use complex jargon

Output only the narration text, nothing else.
"""


class NarrationError(Exception):
    """Raised when narration generation fails."""

    pass


class TTSError(Exception):
    """Raised when text-to-speech synthesis fails."""

    pass


async def generate_narrations(
    models: list[MatchedModel],
    analysis: ContentAnalysis,
    llm: LLM,
) -> dict[str, str]:
    """Generate narration text for each matched model.

    Args:
        models: List of matched 3D models
        analysis: Content analysis from the document
        llm: LLM instance for generation

    Returns:
        Dictionary mapping model ID to narration text
    """
    logger.info("generating_narrations", model_count=len(models))

    narrations: dict[str, str] = {}

    for model in models:
        prompt = NARRATION_PROMPT.format(
            topic=analysis.title,
            model_name=model.name,
            model_description=model.description,
        )

        try:
            response = await llm.generate(prompt)
            narrations[model.id] = response.strip()
            logger.debug("narration_generated", model_id=model.id)
        except Exception as e:
            logger.error("narration_failed", model_id=model.id, error=str(e))
            # Use a fallback narration
            narrations[model.id] = (
                f"This {model.name} represents a key concept from your document. "
                f"Click to explore and learn more about {model.name.lower()}."
            )

    logger.info("narrations_complete", count=len(narrations))
    return narrations


async def synthesize_audio(
    narrations: dict[str, str],
    settings: Settings,
    gcs_client: GCSClient,
) -> dict[str, str]:
    """Convert narration text to audio using ElevenLabs TTS.

    Args:
        narrations: Dictionary mapping model ID to narration text
        settings: Application settings with API keys
        gcs_client: GCS client for uploading audio files

    Returns:
        Dictionary mapping model ID to audio URL (empty dict if TTS unavailable)
    """
    # Skip TTS if no API key or default placeholder
    if not settings.elevenlabs_api_key or "your_elevenlabs_api_key" in settings.elevenlabs_api_key:
        logger.info(
            "tts_skipped",
            reason="no_api_key" if not settings.elevenlabs_api_key else "placeholder_key",
        )
        return {}

    logger.info("synthesizing_audio", narration_count=len(narrations))

    audio_urls: dict[str, str] = {}
    elevenlabs_url = "https://api.elevenlabs.io/v1/text-to-speech"

    async with httpx.AsyncClient() as client:
        for model_id, text in narrations.items():
            try:
                response = await client.post(
                    f"{elevenlabs_url}/{settings.elevenlabs_voice_id}",
                    headers={
                        "Accept": "audio/mpeg",
                        "Content-Type": "application/json",
                        "xi-api-key": settings.elevenlabs_api_key,
                    },
                    json={
                        "text": text,
                        "model_id": "eleven_monolingual_v1",
                        "voice_settings": {
                            "stability": 0.5,
                            "similarity_boost": 0.75,
                        },
                    },
                    timeout=30.0,
                )

                if response.status_code != 200:
                    logger.error(
                        "tts_api_error",
                        model_id=model_id,
                        status=response.status_code,
                        body=response.text[:200],
                    )
                    continue

                audio_bytes = response.content
                filename = f"{model_id}.mp3"
                url = await gcs_client.upload_audio(audio_bytes, filename)
                audio_urls[model_id] = url

                logger.debug("audio_synthesized", model_id=model_id, url=url)

            except Exception as e:
                logger.error("tts_failed", model_id=model_id, error=str(e))
                # Continue with other models even if one fails

    logger.info("audio_synthesis_complete", count=len(audio_urls))
    return audio_urls
