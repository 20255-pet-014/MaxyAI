"""FastMCP tool implementations for the Maxy Writer & Critic Agent."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..app.writer_handler import (
    critic_evaluation_handler,
    draft_section_handler,
    extract_research_metadata,
    generate_outline_handler,
    refine_article_handler,
)
from ..config.settings import settings
from ..utils.file_utils import validate_research_folder

logger = logging.getLogger(__name__)


# ============================================================================
# TOOL 1: READ RESEARCH SUMMARY
# ============================================================================


async def read_research_summary_tool(research_directory: str) -> Dict[str, Any]:
    """
    Read and extract key metadata, guidelines, and source references from research.md.

    Args:
        research_directory: The absolute path to the research directory

    Returns:
        Dict containing guidelines, character counts, and cited source URLs.
    """
    path = Path(research_directory)
    validate_research_folder(path)

    meta = extract_research_metadata(path)
    return {
        "status": "success",
        "research_length_chars": meta["research_length"],
        "total_sources_cited": meta["total_sources_cited"],
        "sample_sources": meta["source_urls"][:10],
        "guidelines_preview": meta["guidelines"][:500] if meta["guidelines"] else "No guidelines found",
        "message": f"Successfully parsed research data from '{path}'. Found {meta['total_sources_cited']} sources across {meta['research_length']} characters.",
    }


# ============================================================================
# TOOL 2: GENERATE ARTICLE OUTLINE
# ============================================================================


async def generate_article_outline_tool(research_directory: str) -> Dict[str, Any]:
    """
    Generate a structured technical outline based on research.md and article_guideline.md.

    Args:
        research_directory: The absolute path to the research directory

    Returns:
        Dict containing article title, subtitle, target audience, and ordered sections.
    """
    path = Path(research_directory)
    validate_research_folder(path)

    # Use configured model (default: llama-3.1-8b)
    outline = await generate_outline_handler(path, model_name=settings.query_generation_model)

    # Save outline to .nova/article_outline.json
    nova_dir = path / ".nova"
    nova_dir.mkdir(exist_ok=True, parents=True)
    outline_path = nova_dir / "article_outline.json"
    outline_dict = outline.model_dump()
    outline_path.write_text(json.dumps(outline_dict, indent=2), encoding="utf-8")

    return {
        "status": "success",
        "outline": outline_dict,
        "saved_path": str(outline_path),
        "total_sections": len(outline.sections),
        "message": f"Generated structured article outline with {len(outline.sections)} sections. Saved to '{outline_path}'.",
    }


# ============================================================================
# TOOL 3: DRAFT ARTICLE SECTION
# ============================================================================


async def draft_article_section_tool(
    research_directory: str,
    section_title: str,
    key_points: List[str],
    include_code: bool = True,
) -> Dict[str, Any]:
    """
    Draft a deep technical article section with runnable code examples and source citations.

    Args:
        research_directory: The absolute path to the research directory
        section_title: The heading / title of the section to write
        key_points: List of core technical concepts and points to address
        include_code: Whether to include realistic, runnable code examples (default: True)

    Returns:
        Dict containing the section markdown text and word count.
    """
    path = Path(research_directory)
    validate_research_folder(path)

    meta = extract_research_metadata(path)
    section_text = await draft_section_handler(
        section_title=section_title,
        key_points=key_points,
        research_context=meta["research_context"],
        guidelines=meta["guidelines"],
        include_code=include_code,
        model_name=settings.scraping_model,
    )

    words = len(section_text.split())
    return {
        "status": "success",
        "section_title": section_title,
        "word_count": words,
        "content": section_text,
        "message": f"Successfully drafted section '{section_title}' ({words} words).",
    }


# ============================================================================
# TOOL 4: CRITIC EVALUATE ARTICLE
# ============================================================================


async def critic_evaluate_article_tool(
    research_directory: str,
    article_content: str,
) -> Dict[str, Any]:
    """
    Critically review an article draft for technical depth, code quality, and factual accuracy.

    Args:
        research_directory: The absolute path to the research directory
        article_content: The full markdown text of the article draft to evaluate

    Returns:
        Dict containing score (0-100), strengths, improvement areas, and revision steps.
    """
    path = Path(research_directory)
    validate_research_folder(path)

    meta = extract_research_metadata(path)
    evaluation = await critic_evaluation_handler(
        article_text=article_content,
        guidelines=meta["guidelines"],
        model_name=settings.source_selection_model,
    )

    eval_dict = evaluation.model_dump()

    # Save critique to .nova/critic_evaluation.json
    nova_dir = path / ".nova"
    nova_dir.mkdir(exist_ok=True, parents=True)
    critique_path = nova_dir / "critic_evaluation.json"
    critique_path.write_text(json.dumps(eval_dict, indent=2), encoding="utf-8")

    return {
        "status": "success",
        "evaluation": eval_dict,
        "overall_score": evaluation.overall_score,
        "saved_path": str(critique_path),
        "message": f"Peer review complete. Overall Quality Score: {evaluation.overall_score}/100. Feedback saved to '{critique_path}'.",
    }


# ============================================================================
# TOOL 5: REFINE AND SAVE ARTICLE
# ============================================================================


async def refine_and_save_article_tool(
    research_directory: str,
    article_content: str,
    critic_feedback: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Apply critic feedback, format Table of Contents, and save final publication article.md.

    Args:
        research_directory: The absolute path to the research directory
        article_content: The current article markdown draft
        critic_feedback: Optional list of specific peer review revisions to apply

    Returns:
        Dict confirming output path, final word count, and file status.
    """
    path = Path(research_directory)
    validate_research_folder(path)

    feedback = critic_feedback or [
        "Ensure crisp formatting with callout blocks (> [!TIP]) and working code samples.",
        "Add a clean Table of Contents and executive summary at the beginning.",
        "Add verified citation links in the references section.",
    ]

    refined_text = await refine_article_handler(
        article_text=article_content,
        critic_feedback=feedback,
        model_name=settings.scraping_model,
    )

    # Save to article.md in research directory
    output_file = path / "article.md"
    output_file.write_text(refined_text, encoding="utf-8")

    words = len(refined_text.split())
    lines = len(refined_text.splitlines())

    return {
        "status": "success",
        "output_file": str(output_file),
        "word_count": words,
        "line_count": lines,
        "message": f"Successfully refined and generated final publication article at '{output_file}' ({words} words, {lines} lines).",
    }
