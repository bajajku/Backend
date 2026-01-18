"""Pydantic request/response models for API endpoints."""

from typing import Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str = "1.0.0"


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str
    error_code: Optional[str] = None


class ModelInfo(BaseModel):
    """Information about a 3D model from GCS."""

    id: str
    url: str
    name: str
    keywords: list[str]
    category: str
    description: str


class ModelManifest(BaseModel):
    """Manifest containing all available 3D models."""

    models: list[ModelInfo]


class MatchedModel(BaseModel):
    """A model matched to document content with relevance score."""

    id: str
    url: str
    name: str
    description: str
    keywords: list[str]
    category: str
    score: int = Field(default=0, description="Relevance score based on keyword matching")


class GenerateRequest(BaseModel):
    """Request parameters for generation (used with form data)."""

    # Additional optional parameters could be added here
    max_models: int = Field(default=5, ge=1, le=10, description="Maximum number of 3D models to include")


class GenerationResult(BaseModel):
    """Result metadata from generation (for logging/debugging)."""

    title: str
    models_used: list[str]
    audio_generated: bool
    html_size_bytes: int
