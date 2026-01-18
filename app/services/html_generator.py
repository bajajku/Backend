"""HTML generation service using LLM to create Three.js scenes."""

import json

import structlog

from app.models.analysis import ContentAnalysis
from app.models.schemas import MatchedModel
from app.utils.llm import LLM

logger = structlog.get_logger()

HTML_GENERATION_PROMPT = """Create an immersive, visually stunning Three.js 3D experience.

SCENE: {title}
THEME: {theme} | COLOR: {background_color} | SUBJECT: {subject_area}

MODELS (each has id, name, url, description, narration_text, audio_url):
{models_json}

IMPORTANT: Each model has an audio_url field - you MUST use it to play narration audio on click!

══════════════════════════════════════════════════════════════
REQUIRED LIBRARIES (include in this exact order):
══════════════════════════════════════════════════════════════
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
<script type="importmap">
{{"imports":{{"three":"https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"}}}}
</script>

Import: THREE, OrbitControls, GLTFLoader, EffectComposer, RenderPass, UnrealBloomPass

══════════════════════════════════════════════════════════════
VISUAL EFFECTS (implement ALL):
══════════════════════════════════════════════════════════════
1. ANIMATED BACKGROUND:
   - Create 200+ particle stars using THREE.Points with random positions
   - Stars slowly drift and twinkle (vary opacity with sine wave)
   - Deep gradient from #0a0a1a to #1a1a3a (or theme color)

2. CINEMATIC LIGHTING:
   - Ambient light (soft, low intensity 0.4)
   - Key directional light (warm white, intensity 1.0, casts shadows)
   - 2-3 colored point lights matching theme (place behind/around models)
   - Subtle spotlight follows selected model

3. POST-PROCESSING:
   - UnrealBloomPass (strength: 0.5, radius: 0.5, threshold: 0.8)
   - Creates soft glow on emissive materials

4. MODEL ANIMATIONS (continuous):
   - Each model floats gently: position.y += Math.sin(time + offset) * 0.05
   - Slow rotation: rotation.y += 0.002
   - Subtle emissive pulse on materials

══════════════════════════════════════════════════════════════
INTERACTIONS (use GSAP for all animations):
══════════════════════════════════════════════════════════════
HOVER:
- gsap.to(model.scale, {{x:1.15, y:1.15, z:1.15, duration:0.3, ease:"back.out"}})
- Increase emissive intensity
- Show floating tooltip near cursor
- Spawn 5-10 tiny particles that fade out

CLICK:
- gsap.to(camera.position, {{...targetPos, duration:1.5, ease:"power2.inOut"}})
- Burst of 20+ particles outward from model
- Model pulses 3 times (scale 1.0→1.1→1.0)
- Other models dim (reduce opacity to 0.3)
- Info panel slides in with glassmorphism effect
- IMPORTANT - Play audio narration:
  ```
  if(currentAudio) currentAudio.pause();
  currentAudio = new Audio(model.userData.audio_url);
  currentAudio.play().catch(e => console.log('Audio:', e));
  ```

DESELECT (click empty space):
- Camera returns to original position
- All models restore full opacity
- Info panel slides out

══════════════════════════════════════════════════════════════
UI DESIGN:
══════════════════════════════════════════════════════════════
- Title: top center, elegant font, text-shadow glow
- Info Panel: glassmorphism (backdrop-filter:blur(10px), rgba bg, border glow)
- Loading: centered spinner with "Loading Experience..." text
- Help hint: "Click models to explore • Drag to rotate" (fades after 5s)
- All UI uses CSS transitions for smooth show/hide

══════════════════════════════════════════════════════════════
TECHNICAL:
══════════════════════════════════════════════════════════════
- Single self-contained HTML file
- Use Raycaster for mouse picking
- Responsive (mobile touch works)
- 60fps animation loop
- Proper error handling for model loading

OUTPUT: Complete HTML only. Start with <!DOCTYPE html>, end with </html>.
No markdown, no explanations.
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
) -> str:
    """Generate complete HTML file with Three.js scene.

    Args:
        analysis: Content analysis from the document
        models: List of matched 3D models
        narrations: Dictionary mapping model ID to narration text
        audio_urls: Dictionary mapping model ID to audio data URIs (base64) or URLs
        llm: LLM instance for generation

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
    )

    # Prepare model data for the prompt
    models_data = []
    for model in models:
        # Audio URLs are now either base64 data URIs or public URLs
        audio_url = audio_urls.get(model.id, "")

        models_data.append(
            {
                "id": model.id,
                "name": model.name,
                "url": model.url,
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
                # Try to repair truncated HTML by closing open tags
                logger.warning("html_truncated_attempting_repair", length=len(html))
                repairs = []
                if "<script" in html and html.count("<script") > html.count("</script>"):
                    repairs.append("\n</script>")
                if "<body" in html and "</body>" not in html:
                    repairs.append("\n</body>")
                if "<html" in html and "</html>" not in html:
                    repairs.append("\n</html>")
                if repairs:
                    html = html + "".join(repairs)
                    logger.info("html_repaired", repairs=repairs)
                else:
                    raise HTMLGenerationError("Invalid HTML output: missing </html>")

        logger.info("html_generation_complete", size_bytes=len(html.encode("utf-8")))
        return html

    except HTMLGenerationError:
        raise
    except Exception as e:
        logger.error("html_generation_failed", error=str(e))
        raise HTMLGenerationError(f"HTML generation failed: {str(e)}") from e
