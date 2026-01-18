"""Content analysis service using LLM."""

import json

import structlog

from app.models.analysis import ContentAnalysis
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
