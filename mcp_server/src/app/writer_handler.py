"""Core logic and schemas for the Maxy Writer & Critic Agent."""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..utils.file_utils import read_file_safe as read_file
from ..utils.llm_utils import get_chat_model

logger = logging.getLogger(__name__)


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================


class ArticleSectionOutline(BaseModel):
    """Schema for an individual section outline."""

    section_id: str = Field(description="Unique section ID, e.g. section_1, section_2")
    title: str = Field(description="Descriptive section heading")
    key_points: List[str] = Field(description="Key technical takeaways and concepts to cover")
    target_word_count: int = Field(default=350, description="Estimated target word count for this section")
    include_code: bool = Field(default=False, description="Whether this section must include a practical code example")
    citations_to_reference: List[str] = Field(
        default_factory=list, description="URLs or sources from research.md to cite"
    )


class ArticleOutline(BaseModel):
    """Schema for the full article outline."""

    title: str = Field(description="Catchy, high-impact technical article title")
    subtitle: str = Field(description="Compelling subtitle summarizing value for senior engineers")
    target_audience: str = Field(description="Target developer/engineer persona")
    estimated_read_time_minutes: int = Field(default=8, description="Estimated reading time in minutes")
    sections: List[ArticleSectionOutline] = Field(description="Ordered list of article sections")


class CriticEvaluation(BaseModel):
    """Schema for the critic evaluation report."""

    overall_score: int = Field(description="Overall quality score between 0 and 100", ge=0, le=100)
    strengths: List[str] = Field(description="Major strengths of the article")
    areas_for_improvement: List[str] = Field(description="Specific technical or stylistic flaws to address")
    factual_citation_check: str = Field(description="Evaluation of citation authenticity and source attribution")
    code_quality_check: str = Field(description="Assessment of code examples, syntax highlighting, and correctness")
    actionable_revisions: List[str] = Field(description="Concrete step-by-step instructions for final polishing")


# ============================================================================
# HANDLER FUNCTIONS
# ============================================================================


def extract_research_metadata(research_path: Path) -> Dict[str, Any]:
    """
    Parse research.md to extract core queries, findings, and citation links.
    """
    research_file = research_path / "research.md"
    guidelines_file = research_path / "article_guideline.md"

    research_text = read_file(research_file) if research_file.exists() else ""
    guidelines_text = read_file(guidelines_file) if guidelines_file.exists() else ""

    # Extract all cited URLs
    urls = list(set(re.findall(r"https?://[^\s\)\>\]]+", research_text)))

    # Truncate research preview to ~6k chars for LLM TPM safety across free-tier models
    truncated_research = research_text[:6_000] if len(research_text) > 6_000 else research_text

    return {
        "guidelines": guidelines_text[:3_000],
        "research_length": len(research_text),
        "total_sources_cited": len(urls),
        "source_urls": urls[:20],
        "research_context": truncated_research,
    }


async def generate_outline_handler(
    research_directory: Path,
    model_name: str = "llama-3.1-8b",
) -> ArticleOutline:
    """
    Generate a structured technical outline based on research.md and article_guideline.md.
    """
    meta = extract_research_metadata(research_directory)
    if not meta["research_context"]:
        raise ValueError(f"No research.md found in {research_directory}. Please run research first.")

    prompt = f"""You are an elite AI technical editor and systems architect.
Create a comprehensive, production-grade technical article outline based on the following research guidelines and data.

### Article Guidelines:
{meta['guidelines']}

### Extracted Research Context:
{meta['research_context']}

Generate a structured outline with a compelling title, subtitle, and ordered sections.
Ensure each section specifies concrete key points, word count targets, and required code examples where applicable.
"""
    chat_model = get_chat_model(model_name, schema=ArticleOutline)
    outline = await chat_model.ainvoke(prompt)
    return outline


async def draft_section_handler(
    section_title: str,
    key_points: List[str],
    research_context: str,
    guidelines: str,
    include_code: bool = True,
    model_name: str = "llama-3.1-8b",
) -> str:
    """
    Draft a single in-depth technical section with concrete explanations and code examples.
    """
    prompt = f"""You are an expert technical author writing a section for a high-impact software engineering article.

### Section Title:
{section_title}

### Key Points to Cover:
- """ + "\n- ".join(key_points) + f"""

### Editorial Guidelines:
{guidelines[:1500]}

### Source Research Context:
{research_context[:3000]}

### Requirements:
1. Write with high technical rigor, deep clarity, and engaging prose.
2. Avoid generic platitudes or fluff. Explain the 'why' and architectural trade-offs.
{"3. Provide realistic, runnable code examples with full comments and best practices." if include_code else "3. Structure the explanation with clear visual bullet points or comparison tables."}
4. Integrate inline citation references where appropriate.

Draft this section now in markdown:
"""
    chat_model = get_chat_model(model_name)
    response = await chat_model.ainvoke(prompt)
    return response.content if hasattr(response, "content") else str(response)


async def critic_evaluation_handler(
    article_text: str,
    guidelines: str,
    model_name: str = "llama-3.1-8b",
) -> CriticEvaluation:
    """
    Evaluate an article draft against technical accuracy, code quality, and guidelines.
    """
    prompt = f"""You are a ruthless, world-class technical peer reviewer and editorial critic.
Critically review the following technical article draft against the target guidelines.

### Target Guidelines:
{guidelines[:2000]}

### Article Draft to Review:
{article_text[:6000]}

### Review Criteria:
1. Technical depth and accuracy (Does it explain core concepts deeply or just skim the surface?)
2. Code quality (Are code examples idiomatic, modern, commented, and syntactically valid?)
3. Structure and flow (Is there a logical progression from fundamentals to advanced patterns?)
4. Citations & Attribution (Are sources credited?)
5. Score objectively between 0 and 100.

Provide a comprehensive, constructive critique with actionable revision items:
"""
    chat_model = get_chat_model(model_name, schema=CriticEvaluation)
    evaluation = await chat_model.ainvoke(prompt)
    return evaluation


async def refine_article_handler(
    article_text: str,
    critic_feedback: List[str],
    model_name: str = "llama-3.1-8b",
) -> str:
    """
    Refine and polish the article by addressing all critic feedback items.
    """
    prompt = f"""You are a master technical editor.
Refine, polish, and enhance the technical article below to incorporate the following peer review recommendations.

### Peer Review Feedback to Address:
- """ + "\n- ".join(critic_feedback) + f"""

### Current Article Text:
{article_text[:6000]}

### Instructions:
1. Add an executive Table of Contents at the top.
2. Fix all noted weaknesses, expanding technical depth and improving code blocks.
3. Ensure crisp formatting, clear markdown headers, callout boxes (e.g. > [!TIP], > [!NOTE]), and comprehensive summaries.
4. Output the complete, final publication-ready markdown article:
"""
    chat_model = get_chat_model(model_name)
    response = await chat_model.ainvoke(prompt)
    return response.content if hasattr(response, "content") else str(response)
