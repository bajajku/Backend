"""Content analysis service using LLM."""

import json

import structlog

from app.models.analysis import ContentAnalysis, ConceptGraph
from app.utils.llm import LLM

logger = structlog.get_logger()

ANALYSIS_PROMPT = """Analyze this educational document and return a JSON object with the following structure:

{{
  "title": "descriptive title for the 3D scene",
  "main_topics": ["topic1", "topic2"],
  "key_concepts": [
    {{"name": "concept", "description": "brief desc", "importance": 1-5}}
  ],
  "subject_area": "biology|physics|chemistry|history|geography|astronomy|anatomy|engineering|mathematics|general",
  "difficulty_level": "beginner|intermediate|advanced",
  "suggested_model_keywords": ["keyword1", "keyword2", "keyword3"],
  "visual_theme": {{
    "primary_color": "#hex",
    "mood": "scientific|playful|serious|exploratory"
  }}
}}

Requirements:
- title: Create a descriptive, engaging title for an interactive 3D learning experience
- main_topics: List 2-5 main topics covered
- key_concepts: Extract 3-7 key concepts with importance ratings
- subject_area: Choose the most appropriate category
- suggested_model_keywords: Provide 5-10 keywords that would match relevant 3D models
- visual_theme: Choose colors and mood appropriate for the subject matter

IMPORTANT: Return ONLY valid JSON, no additional text or markdown.

DOCUMENT CONTENT:
{content}
"""


class AnalysisError(Exception):
    """Raised when content analysis fails."""

    pass


async def analyze_content(content: str, llm: LLM) -> ContentAnalysis:
    """Analyze document content using LLM to extract structure and themes.

    Args:
        content: The extracted text content from the document
        llm: LLM instance for generation

    Returns:
        ContentAnalysis with extracted information

    Raises:
        AnalysisError: If analysis fails
    """
    logger.info("analyzing_content", content_length=len(content))

    # Truncate content if too long (keep first 15000 chars)
    truncated_content = content[:15000]
    if len(content) > 15000:
        logger.info("content_truncated", original=len(content), truncated=15000)

    prompt = ANALYSIS_PROMPT.format(content=truncated_content)

    try:
        response = await llm.generate_json(prompt)
        data = json.loads(response)
        analysis = ContentAnalysis.model_validate(data)

        logger.info(
            "analysis_complete",
            title=analysis.title,
            topics=len(analysis.main_topics),
            concepts=len(analysis.key_concepts),
            subject=analysis.subject_area,
        )

        return analysis

    except json.JSONDecodeError as e:
        logger.error("analysis_json_parse_failed", error=str(e))
        raise AnalysisError(f"Failed to parse LLM response as JSON: {str(e)}") from e
    except Exception as e:
        logger.error("analysis_failed", error=str(e))
        raise AnalysisError(f"Content analysis failed: {str(e)}") from e


# ============================================================
# NEW: Concept Graph Extraction for LLM-Generated 3D Scenes
# ============================================================

CONCEPT_GRAPH_PROMPT = """You are an expert at extracting knowledge structures from educational content.
Analyze this document and create a concept graph that will be visualized in 3D.

Your goal: Extract the KEY CONCEPTS and their RELATIONSHIPS to create a meaningful 3D learning experience.

Return a JSON object with this EXACT structure:

{{
  "title": "Engaging title for the 3D experience",
  "summary": "2-3 sentence summary of what the user will learn",
  "subject_area": "biology|physics|chemistry|history|anatomy|mathematics|general|etc",

  "layout_type": "concept-map|hierarchy|timeline|clusters|network",

  "central_concept_id": "main_concept",

  "concepts": [
    {{
      "id": "unique_id",
      "name": "Display Name",
      "description": "Clear explanation (2-3 sentences). This will be read aloud.",
      "category": "category_id",
      "importance": 5,
      "parent_id": null,
      "shape": "sphere",
      "color": null
    }}
  ],

  "relationships": [
    {{
      "from_id": "concept_a",
      "to_id": "concept_b",
      "relationship_type": "relates_to",
      "label": "optional label",
      "strength": 3
    }}
  ],

  "categories": [
    {{
      "id": "category_id",
      "name": "Category Name",
      "color": "#3498db",
      "description": "What this category represents"
    }}
  ],

  "background_color": "#0a0a1a",
  "ambient_color": "#ffffff",

  "particle_visualization": {{
    "description": "Brief description of what shape/visualization this creates",
    "particle_count": 1500,
    "colors": ["#6ea8fe", "#4ecdc4", "#45b7d1"],
    "generator_code": "JavaScript code that returns array of {{x, y, z}} particle positions",
    "animation_code": "Optional: custom animation code for the particles"
  }},

  "suggested_exploration_order": ["id1", "id2", "id3"]
}}

GUIDELINES:

1. CONCEPTS (5-12 concepts ideal):
   - Extract the most important concepts that someone should understand
   - Each concept needs a clear, accessible description (for audio narration)
   - importance: 5 = central/critical, 1 = supplementary
   - Shapes: sphere (default), box (containers/categories), cylinder (processes), cone (hierarchies), octahedron (key decisions)

2. RELATIONSHIPS:
   - Show how concepts connect and influence each other
   - Types: contains, relates_to, causes, part_of, leads_to, contrasts, supports
   - strength: 5 = strong connection, 1 = weak connection

3. LAYOUT TYPE:
   - concept-map: Central idea with related concepts around it (default, good for most)
   - hierarchy: Tree structure (good for taxonomies, org charts)
   - timeline: Linear sequence (good for history, processes)
   - clusters: Grouped by category (good for comparing groups)
   - network: Free connections (good for complex interrelationships)

4. CATEGORIES:
   - Group related concepts with colors
   - Choose distinct, accessible colors
   - 2-5 categories is ideal

5. EXPLORATION ORDER:
   - Suggest a logical learning path through the concepts
   - Start with foundational concepts, build to complex ones

6. PARTICLE VISUALIZATION (IMPORTANT - be creative!):
   Create a content-aware animated background that visually represents the document's theme.
   
   The generator_code must be a JavaScript function body that:
   - Uses 'count' variable (the particle count)
   - Returns an array of objects with x, y, z coordinates
   - Creates a shape/pattern related to the content
   
   Examples:
   - Brain/Neuroscience: Create a brain-like network with neural connections
   - DNA/Genetics: Create a double helix spiral
   - Solar System/Astronomy: Create orbital rings with clustered particles
   - Chemistry/Molecules: Create molecular bond structures
   - History/Timeline: Create flowing particles along a path
   - Physics/Waves: Create wave patterns
   - Mathematics: Create geometric patterns like fractals or spirals
   - Biology/Cells: Create cell-like circular structures
   
   Example generator_code for a DNA helix:
   ```
   const particles = [];
   for (let i = 0; i < count; i++) {{
     const t = (i / count) * Math.PI * 6;
     const strand = i % 2;
     const radius = 2;
     particles.push({{
       x: Math.cos(t + strand * Math.PI) * radius,
       y: (i / count) * 20 - 10,
       z: Math.sin(t + strand * Math.PI) * radius
     }});
   }}
   return particles;
   ```
   
   Example generator_code for a brain-like neural network:
   ```
   const particles = [];
   for (let i = 0; i < count; i++) {{
     const theta = Math.random() * Math.PI * 2;
     const phi = Math.acos(2 * Math.random() - 1);
     const r = 4 * (0.8 + Math.random() * 0.4);
     const stretch = 0.75;
     particles.push({{
       x: r * Math.sin(phi) * Math.cos(theta),
       y: r * Math.sin(phi) * Math.sin(theta) * stretch,
       z: r * Math.cos(phi) * 0.9
     }});
   }}
   return particles;
   ```
   
   The animation_code is optional JavaScript that runs each frame with access to:
   - 'particles': the THREE.Points object
   - 'time': elapsed time in seconds
   - 'positions': the position attribute array

DOCUMENT CONTENT:
{content}

Return ONLY valid JSON. No markdown, no explanation."""



async def extract_concept_graph(content: str, llm: LLM) -> ConceptGraph:
    """Extract a concept graph from document content.

    This creates a structured representation of concepts and their
    relationships that can be visualized in 3D.

    Args:
        content: The extracted text content from the document
        llm: LLM instance for generation

    Returns:
        ConceptGraph with nodes, relationships, and layout info

    Raises:
        AnalysisError: If extraction fails
    """
    logger.info("extracting_concept_graph", content_length=len(content))

    # Truncate content if too long
    truncated_content = content[:15000]
    if len(content) > 15000:
        logger.info("content_truncated", original=len(content), truncated=15000)

    prompt = CONCEPT_GRAPH_PROMPT.format(content=truncated_content)

    try:
        response = await llm.generate_json(prompt)
        data = json.loads(response)
        graph = ConceptGraph.model_validate(data)

        logger.info(
            "concept_graph_extracted",
            title=graph.title,
            concepts=len(graph.concepts),
            relationships=len(graph.relationships),
            categories=len(graph.categories),
            layout=graph.layout_type,
        )

        return graph

    except json.JSONDecodeError as e:
        logger.error("concept_graph_json_parse_failed", error=str(e))
        raise AnalysisError(f"Failed to parse concept graph JSON: {str(e)}") from e
    except Exception as e:
        logger.error("concept_graph_extraction_failed", error=str(e))
        raise AnalysisError(f"Concept graph extraction failed: {str(e)}") from e
