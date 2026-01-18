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


# ============================================================
# NEW: Concept Graph Models for LLM-Generated 3D Scenes
# ============================================================


class ConceptNode(BaseModel):
    """A concept node in the knowledge graph."""

    id: str = Field(description="Unique identifier for the concept")
    name: str = Field(description="Display name")
    description: str = Field(description="Full description/explanation")
    category: str = Field(description="Category for grouping and coloring")
    importance: int = Field(ge=1, le=5, default=3, description="Importance 1-5")
    parent_id: str | None = Field(default=None, description="Parent concept ID if hierarchical")
    shape: Literal["sphere", "box", "cylinder", "cone", "torus", "octahedron"] = Field(
        default="sphere", description="3D shape to represent this concept"
    )
    color: str | None = Field(default=None, description="Specific color override (hex)")


class ConceptRelationship(BaseModel):
    """A relationship between two concepts."""

    from_id: str = Field(description="Source concept ID")
    to_id: str = Field(description="Target concept ID")
    relationship_type: Literal[
        "contains",      # parent contains child
        "relates_to",    # general relationship
        "causes",        # cause and effect
        "part_of",       # part-whole relationship
        "leads_to",      # sequential/temporal
        "contrasts",     # opposing concepts
        "supports",      # supporting evidence
    ] = Field(default="relates_to")
    label: str | None = Field(default=None, description="Optional label for the connection")
    strength: int = Field(ge=1, le=5, default=3, description="Relationship strength 1-5")


class ConceptCategory(BaseModel):
    """A category for grouping concepts."""

    id: str
    name: str
    color: str = Field(description="Hex color for this category")
    description: str | None = None


class ParticleVisualization(BaseModel):
    """LLM-generated particle system for content-aware background animations."""

    description: str = Field(
        description="Brief description of what the particle visualization represents"
    )
    particle_count: int = Field(
        default=1500,
        ge=500,
        le=5000,
        description="Number of particles (500-5000)"
    )
    colors: list[str] = Field(
        default_factory=lambda: ["#6ea8fe", "#4ecdc4"],
        description="List of hex colors for particles"
    )
    generator_code: str = Field(
        description="JavaScript function body that generates particle positions. Must return array of {x, y, z} objects."
    )
    animation_code: str | None = Field(
        default=None,
        description="Optional JavaScript code for custom particle animation in the render loop"
    )


class ConceptGraph(BaseModel):
    """Complete concept graph extracted from document."""

    title: str = Field(description="Title for the 3D experience")
    summary: str = Field(description="Brief summary of the document (2-3 sentences)")
    subject_area: str = Field(description="Subject area")

    # Layout recommendation
    layout_type: Literal[
        "concept-map",   # Central concept with orbiting related concepts
        "hierarchy",     # Tree structure for hierarchical content
        "timeline",      # Linear progression for sequential content
        "clusters",      # Grouped by categories
        "network",       # Free-form network of relationships
    ] = Field(default="concept-map")

    # The graph data
    central_concept_id: str = Field(description="ID of the main/central concept")
    concepts: list[ConceptNode] = Field(description="All concept nodes")
    relationships: list[ConceptRelationship] = Field(description="Relationships between concepts")
    categories: list[ConceptCategory] = Field(description="Categories for grouping")

    # Visual theme
    background_color: str = Field(default="#0a0a1a", description="Scene background color")
    ambient_color: str = Field(default="#ffffff", description="Ambient light color")

    # Content-aware particle visualization (LLM-generated)
    particle_visualization: ParticleVisualization | None = Field(
        default=None,
        description="Optional LLM-generated particle system for content-aware background"
    )

    # Learning path (optional)
    suggested_exploration_order: list[str] = Field(
        default_factory=list,
        description="Suggested order to explore concepts (list of IDs)"
    )
