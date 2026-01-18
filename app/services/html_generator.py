"""HTML generation service using LLM to create Three.js scenes."""

import json

import structlog

from app.models.analysis import ContentAnalysis
from app.models.schemas import MatchedModel
from app.utils.llm import LLM

logger = structlog.get_logger()

HTML_GENERATION_PROMPT = """Generate a complete, self-contained HTML file with an interactive Three.js 3D scene.

SCENE CONFIGURATION:
- Title: {title}
- Theme/Mood: {theme}
- Background color: {background_color}
- Subject area: {subject_area}

3D MODELS TO LOAD (GLTF format):
{models_json}

NARRATIONS (play on model click):
{narrations_json}

REQUIREMENTS:
1. Use Three.js from CDN (version r160 or newer)
2. Use GLTFLoader from Three.js addons CDN
3. Load all GLTF models from the provided URLs
4. Position models in a logical circular or grid layout with good spacing
5. Implement OrbitControls for camera rotation/zoom
6. Hover effects:
   - Scale model to 1.1x on hover
   - Show tooltip with model name
   - Change cursor to pointer
7. Click effects:
   - Play narration audio for that model
   - Animate camera to focus on clicked model
   - Add subtle pulse/glow animation
   - Show narration text in a panel
8. Style the page to match the visual theme:
   - Use the primary color for accents
   - Match the mood (scientific=clean/minimal, playful=colorful, etc.)
9. Include a loading indicator while models load
10. Accessibility features:
    - Keyboard navigation (Tab to cycle models, Enter to select)
    - ARIA labels on interactive elements
    - Focus indicators
    - Screen reader announcements for narrations
11. Responsive design that works on mobile
12. Add a title overlay showing the scene title
13. Include a help tooltip explaining controls

STYLING GUIDELINES:
- Use modern CSS with flexbox/grid
- Smooth transitions and animations
- Clean, readable fonts (system fonts or Google Fonts CDN)
- Semi-transparent panels for UI elements
- Good contrast for accessibility

TECHNICAL REQUIREMENTS:
- All code must be in a single HTML file
- No external dependencies except CDN links
- Use async/await for loading
- Handle loading errors gracefully
- Dispose of Three.js resources properly

OUTPUT: Return ONLY the complete HTML file.
Start exactly with <!DOCTYPE html> and end exactly with </html>.
Do not include any markdown, explanations, or other text.
"""


class HTMLGenerationError(Exception):
    """Raised when HTML generation fails."""

    pass


async def generate_html(
    analysis: ContentAnalysis,
    models: list[MatchedModel],
    narrations: dict[str, str],
    audio_urls: dict[str, str],
    llm: LLM,
    base_url: str = "",
) -> str:
    """Generate complete HTML file with Three.js scene.

    Args:
        analysis: Content analysis from the document
        models: List of matched 3D models
        narrations: Dictionary mapping model ID to narration text
        audio_urls: Dictionary mapping model ID to audio URLs
        llm: LLM instance for generation
        base_url: Base URL for resolving relative assets (used in local mode)

    Returns:
        Complete HTML file as a string

    Raises:
        HTMLGenerationError: If generation fails
    """
    logger.info(
        "generating_html",
        title=analysis.title,
        model_count=len(models),
        has_audio=bool(audio_urls),
        base_url=base_url,
    )

    # Prepare model data for the prompt
    models_data = []
    for model in models:
        # Prepend base_url to relative URLs (e.g., /static/...)
        model_url = model.url
        if base_url and model_url.startswith("/"):
            model_url = f"{base_url}{model_url}"

        audio_url = audio_urls.get(model.id, "")
        if base_url and audio_url.startswith("/"):
            audio_url = f"{base_url}{audio_url}"

        models_data.append(
            {
                "id": model.id,
                "name": model.name,
                "url": model_url,
                "description": model.description,
                "narration_text": narrations.get(model.id, ""),
                "audio_url": audio_url,
            }
        )

    prompt = HTML_GENERATION_PROMPT.format(
        title=analysis.title,
        theme=analysis.visual_theme.mood,
        background_color=analysis.visual_theme.primary_color,
        subject_area=analysis.subject_area,
        models_json=json.dumps(models_data, indent=2),
        narrations_json=json.dumps(narrations, indent=2),
    )

    try:
        html = await llm.generate(prompt)

        # Clean up the response
        html = html.strip()

        # Remove markdown code blocks if present
        if html.startswith("```html"):
            html = html[7:]
        elif html.startswith("```"):
            html = html[3:]
        if html.endswith("```"):
            html = html[:-3]

        html = html.strip()

        # Validate HTML structure
        if not html.startswith("<!DOCTYPE html>"):
            # Try to find DOCTYPE in the response
            doctype_pos = html.find("<!DOCTYPE html>")
            if doctype_pos != -1:
                html = html[doctype_pos:]
            else:
                raise HTMLGenerationError(
                    "Invalid HTML output: missing <!DOCTYPE html>"
                )

        if not html.rstrip().endswith("</html>"):
            # Try to find closing tag
            html_end = html.rfind("</html>")
            if html_end != -1:
                html = html[: html_end + 7]
            else:
                raise HTMLGenerationError("Invalid HTML output: missing </html>")

        logger.info("html_generation_complete", size_bytes=len(html.encode("utf-8")))
        return html

    except HTMLGenerationError:
        raise
    except Exception as e:
        logger.error("html_generation_failed", error=str(e))
        raise HTMLGenerationError(f"HTML generation failed: {str(e)}") from e
