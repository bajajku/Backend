"""API router for document-to-3D generation endpoints."""

import tempfile
from pathlib import Path
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse

from app.config import Settings, get_settings
from app.models.schemas import HealthResponse, MatchedModel, ModelInfo
from app.services.analysis import AnalysisError, analyze_content, extract_concept_graph
from app.services.extraction import (
    ExtractionError,
    extract_content,
    is_supported_mime_type,
)
from app.services.html_generator import HTMLGenerationError, generate_html
from app.services.matching import match_models
from app.services.narration import generate_narrations, synthesize_audio
from app.services.scene_generator import generate_primitive_scene_html
from app.utils.gcs import GCSClient
from app.utils.llm import LLM

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1", tags=["generation"])


class Services:
    """Container for shared service instances."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.llm = LLM(settings)
        self.gcs = GCSClient(settings)
        self._manifest_cache = None

    async def get_manifest(self):
        """Get cached model manifest."""
        if self._manifest_cache is None:
            self._manifest_cache = await self.gcs.get_manifest()
        return self._manifest_cache


_services: Services | None = None


def get_services(settings: Annotated[Settings, Depends(get_settings)]) -> Services:
    """Get or create services instance."""
    global _services
    if _services is None:
        _services = Services(settings)
    return _services


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Check service health status."""
    return HealthResponse(status="healthy", version="1.0.0")


@router.get("/models", response_model=list[ModelInfo])
async def list_models(
    services: Annotated[Services, Depends(get_services)],
) -> list[ModelInfo]:
    """List all available 3D models from GCS manifest."""
    try:
        manifest = await services.get_manifest()
        return manifest.models
    except Exception as e:
        logger.error("models_list_failed", error=str(e))
        raise HTTPException(status_code=503, detail="Failed to fetch model manifest")


@router.post("/generate")
async def generate_3d_experience(
    file: Annotated[UploadFile, File(description="Document file (PDF, PPTX, or TXT)")],
    services: Annotated[Services, Depends(get_services)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> HTMLResponse:
    """Generate interactive 3D HTML from uploaded document.

    Accepts PDF, PPTX, or TXT files and returns a self-contained HTML file
    with an interactive Three.js 3D scene, narrations, and audio.
    """
    logger.info(
        "generate_request",
        filename=file.filename,
        content_type=file.content_type,
    )

    # Validate file type
    if not file.content_type or not is_supported_mime_type(file.content_type):
        raise HTTPException(
            status_code=400,
            detail={
                "detail": f"Unsupported file type: {file.content_type}",
                "error_code": "UNSUPPORTED_FILE_TYPE",
            },
        )

    # Check file size
    content = await file.read()
    if len(content) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=413,
            detail={
                "detail": f"File too large. Maximum size: {settings.max_file_size_mb}MB",
                "error_code": "FILE_TOO_LARGE",
            },
        )

    # Save to temporary file
    suffix = Path(file.filename).suffix if file.filename else ".tmp"
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp_path = Path(tmp_file.name)

    try:
        tmp_file.write(content)
        tmp_file.close()

        # Step 1: Extract content
        try:
            text = await extract_content(tmp_path, file.content_type)
        except ExtractionError as e:
            raise HTTPException(
                status_code=422,
                detail={"detail": str(e), "error_code": "EXTRACTION_FAILED"},
            )

        if not text.strip():
            raise HTTPException(
                status_code=422,
                detail={
                    "detail": "No text content found in document",
                    "error_code": "EMPTY_DOCUMENT",
                },
            )

        # Step 2: Analyze content
        try:
            analysis = await analyze_content(text, services.llm)
        except AnalysisError as e:
            raise HTTPException(
                status_code=500,
                detail={"detail": str(e), "error_code": "ANALYSIS_FAILED"},
            )

        # Step 3: Match models
        manifest = await services.get_manifest()
        models: list[MatchedModel] = await match_models(analysis, manifest)

        if not models:
            raise HTTPException(
                status_code=422,
                detail={
                    "detail": "No matching 3D models found for document content",
                    "error_code": "NO_MATCHING_MODELS",
                },
            )

        # Step 4: Generate narrations
        narrations = await generate_narrations(models, analysis, services.llm)

        # Step 5: Synthesize audio (returns both URLs and base64)
        audio_result = await synthesize_audio(narrations, settings, services.gcs)

        # Step 6: Generate HTML (use short URLs in prompt, not huge base64)
        try:
            html = await generate_html(
                analysis,
                models,
                narrations,
                audio_result.urls,  # Use URLs for LLM prompt (small)
                services.llm,
            )

            # Post-process: Replace URLs with base64 for offline capability
            for model_id, url in audio_result.urls.items():
                if model_id in audio_result.base64:
                    html = html.replace(url, audio_result.base64[model_id])
        except HTMLGenerationError as e:
            raise HTTPException(
                status_code=500,
                detail={"detail": str(e), "error_code": "HTML_GENERATION_FAILED"},
            )

        # Create safe filename
        safe_title = "".join(
            c if c.isalnum() or c in " -_" else "_" for c in analysis.title
        )
        safe_title = safe_title.replace(" ", "_")[:50]
        filename = f"{safe_title}_3D.html"

        logger.info(
            "generation_complete",
            title=analysis.title,
            models_used=[m.id for m in models],
            html_size=len(html),
        )

        return HTMLResponse(
            content=html,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    finally:
        # Cleanup temp file
        try:
            tmp_path.unlink()
        except Exception:
            pass


# ============================================================
# NEW: Primitive-based 3D Generation (v2)
# ============================================================


@router.post("/generate-v2")
async def generate_3d_experience_v2(
    file: Annotated[UploadFile, File(description="Document file (PDF, PPTX, or TXT)")],
    services: Annotated[Services, Depends(get_services)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> HTMLResponse:
    """Generate interactive 3D HTML using concept-based primitives.

    This is the NEW approach that:
    - Extracts concepts and relationships from the document
    - Creates meaningful 3D visualizations using primitives (no external models)
    - Provides actual educational value with proper spatial relationships

    Accepts PDF, PPTX, or TXT files and returns a self-contained HTML file.
    """
    logger.info(
        "generate_v2_request",
        filename=file.filename,
        content_type=file.content_type,
    )

    # Validate file type
    if not file.content_type or not is_supported_mime_type(file.content_type):
        raise HTTPException(
            status_code=400,
            detail={
                "detail": f"Unsupported file type: {file.content_type}",
                "error_code": "UNSUPPORTED_FILE_TYPE",
            },
        )

    # Check file size
    content = await file.read()
    if len(content) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=413,
            detail={
                "detail": f"File too large. Maximum size: {settings.max_file_size_mb}MB",
                "error_code": "FILE_TOO_LARGE",
            },
        )

    # Save to temporary file
    suffix = Path(file.filename).suffix if file.filename else ".tmp"
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp_path = Path(tmp_file.name)

    try:
        tmp_file.write(content)
        tmp_file.close()

        # Step 1: Extract content
        try:
            text = await extract_content(tmp_path, file.content_type)
        except ExtractionError as e:
            raise HTTPException(
                status_code=422,
                detail={"detail": str(e), "error_code": "EXTRACTION_FAILED"},
            )

        if not text.strip():
            raise HTTPException(
                status_code=422,
                detail={
                    "detail": "No text content found in document",
                    "error_code": "EMPTY_DOCUMENT",
                },
            )

        # Step 2: Extract concept graph (NEW!)
        try:
            concept_graph = await extract_concept_graph(text, services.llm)
        except AnalysisError as e:
            raise HTTPException(
                status_code=500,
                detail={"detail": str(e), "error_code": "CONCEPT_EXTRACTION_FAILED"},
            )

        # Step 3: Generate audio narrations for each concept
        narrations = {c.id: c.description for c in concept_graph.concepts}
        audio_result = await synthesize_audio(narrations, settings, services.gcs)

        # Step 4: Generate HTML with primitives (no external models!)
        html = generate_primitive_scene_html(concept_graph, audio_result.base64)

        # Create safe filename
        safe_title = "".join(
            c if c.isalnum() or c in " -_" else "_" for c in concept_graph.title
        )
        safe_title = safe_title.replace(" ", "_")[:50]
        filename = f"{safe_title}_3D.html"

        logger.info(
            "generation_v2_complete",
            title=concept_graph.title,
            concepts=len(concept_graph.concepts),
            relationships=len(concept_graph.relationships),
            layout=concept_graph.layout_type,
            html_size=len(html),
        )

        return HTMLResponse(
            content=html,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    finally:
        # Cleanup temp file
        try:
            tmp_path.unlink()
        except Exception:
            pass
