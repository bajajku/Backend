"""Content analysis models for LLM output parsing."""

from typing import Literal

from pydantic import BaseModel, Field


class KeyConcept(BaseModel):
    """A key concept extracted from the document."""

    name: str
    description: str
    importance: int = Field(ge=1, le=5, description="Importance level from 1-5")


class VisualTheme(BaseModel):
    """Visual theme configuration for the 3D scene."""

    primary_color: str = Field(default="#1a1a2e", description="Hex color code")
    mood: Literal["scientific", "playful", "serious", "exploratory"] = "exploratory"


class ContentAnalysis(BaseModel):
    """Complete analysis of document content by LLM."""

    title: str = Field(description="Descriptive title for the 3D scene")
    main_topics: list[str] = Field(description="Main topics covered in the document")
    key_concepts: list[KeyConcept] = Field(description="Key concepts with descriptions")
    subject_area: Literal[
        "biology",
        "physics",
        "chemistry",
        "history",
        "geography",
        "astronomy",
        "anatomy",
        "engineering",
        "mathematics",
        "general",
    ] = Field(description="Primary subject area of the document")
    difficulty_level: Literal["beginner", "intermediate", "advanced"] = Field(
        description="Difficulty level of the content"
    )
    suggested_model_keywords: list[str] = Field(
        description="Keywords to search for matching 3D models"
    )
    visual_theme: VisualTheme = Field(
        default_factory=VisualTheme, description="Visual theme for the scene"
    )


class NarrationData(BaseModel):
    """Narration data for a single model."""

    model_id: str
    text: str
    audio_url: str | None = None
