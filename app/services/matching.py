"""Model matching service for selecting 3D models based on document content."""

import structlog

from app.models.analysis import ContentAnalysis
from app.models.schemas import MatchedModel, ModelManifest

logger = structlog.get_logger()


async def match_models(
    analysis: ContentAnalysis,
    manifest: ModelManifest,
    max_models: int = 5,
) -> list[MatchedModel]:
    """Score and select best matching models based on keyword overlap.

    Args:
        analysis: Content analysis from the document
        manifest: Available 3D models from GCS
        max_models: Maximum number of models to return

    Returns:
        List of matched models sorted by relevance score
    """
    logger.info(
        "matching_models",
        keywords=analysis.suggested_model_keywords,
        topics=analysis.main_topics,
        subject=analysis.subject_area,
        available_models=len(manifest.models),
    )

    # Build search terms from analysis
    search_terms = set(
        [term.lower() for term in analysis.suggested_model_keywords]
        + [topic.lower() for topic in analysis.main_topics]
        + [analysis.subject_area.lower()]
    )

    # Add key concept names to search terms
    for concept in analysis.key_concepts:
        search_terms.add(concept.name.lower())

    scored_models: list[tuple[int, MatchedModel]] = []

    for model in manifest.models:
        # Build model terms
        model_terms = set(
            [kw.lower() for kw in model.keywords] + [model.category.lower()]
        )

        # Also check model name and description for matches
        model_name_words = set(model.name.lower().split())
        model_desc_words = set(model.description.lower().split())

        # Calculate overlap score
        keyword_overlap = len(search_terms & model_terms)
        name_overlap = len(search_terms & model_name_words)
        desc_overlap = len(search_terms & model_desc_words)

        # Weight keyword matches higher than name/description
        score = keyword_overlap * 3 + name_overlap * 2 + desc_overlap

        # Bonus for matching subject area/category
        if model.category.lower() == analysis.subject_area.lower():
            score += 5

        if score > 0:
            matched = MatchedModel(
                id=model.id,
                url=model.url,
                name=model.name,
                description=model.description,
                keywords=model.keywords,
                category=model.category,
                score=score,
            )
            scored_models.append((score, matched))

    # Sort by score descending
    scored_models.sort(key=lambda x: x[0], reverse=True)

    # Take top N models
    result = [model for _, model in scored_models[:max_models]]

    logger.info(
        "matching_complete",
        matched_count=len(result),
        top_scores=[m.score for m in result],
    )

    return result
