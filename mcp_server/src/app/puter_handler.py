"""Puter AI operations and utilities for free Perplexity access."""

import logging
import re
from typing import Dict, List, Tuple

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from ..config.prompts import PROMPT_WEB_SEARCH
from ..config.settings import settings

logger = logging.getLogger(__name__)


class SourceAnswer(BaseModel):
    """A single source answer with URL and content."""

    url: str = Field(description="The URL of the source")
    answer: str = Field(description="The detailed answer extracted from that source")


class PuterPerplexityResponse(BaseModel):
    """Structured response from Puter Perplexity search containing multiple sources."""

    sources: List[SourceAnswer] = Field(description="List of sources with their answers")


def parse_raw_puter_text(content: str) -> Tuple[str, Dict[int, str], Dict[int, str]]:
    """Fallback parser if structured output is not returned directly."""
    answer_by_source: Dict[int, str] = {}
    citations: Dict[int, str] = {}

    url_pattern = re.compile(r"https?://[^\s)\]]+", re.IGNORECASE)
    raw_urls = url_pattern.findall(content)
    # Strip trailing punctuation (e.g. ',', '.', ';', '"', '\'')
    cleaned_urls = [re.sub(r"[,.;:\'\"<>]+$", "", u) for u in raw_urls]
    urls = list(dict.fromkeys([u for u in cleaned_urls if u]))

    if urls:
        for idx, url in enumerate(urls, 1):
            citations[idx] = url
            answer_by_source[idx] = content
    else:
        citations[1] = "https://search.puter.com"
        answer_by_source[1] = content

    full_answer_lines = []
    for idx, url in citations.items():
        full_answer_lines.append(f"### [{idx}]: {url}")
        full_answer_lines.append(answer_by_source[idx])
        full_answer_lines.append("")

    return "\n".join(full_answer_lines), answer_by_source, citations


async def run_puter_search(query: str) -> Tuple[str, Dict[int, str], Dict[int, str]]:
    """Run a Perplexity search via Puter's OpenAI-compatible endpoint ($0 budget)."""
    auth_token = None
    if settings.puter_auth_token:
        auth_token = settings.puter_auth_token.get_secret_value()
    elif settings.perplexity_api_key:
        auth_token = settings.perplexity_api_key.get_secret_value()

    if not auth_token:
        raise RuntimeError(
            "PUTER_AUTH_TOKEN environment variable not set. "
            "Get a free token from https://puter.com/dashboard and set PUTER_AUTH_TOKEN=your_token."
        )

    model_name = settings.puter_model or "perplexity/sonar"
    prompt = PROMPT_WEB_SEARCH.format(query=query)
    logger.debug(f"Searching web via Puter AI ({model_name}) for: {query} …")

    llm = ChatOpenAI(
        base_url="https://api.puter.com/puterai/openai/v1/",
        api_key=auth_token,
        model=model_name,
        temperature=0.7,
        max_retries=3,
    )

    try:
        structured_llm = llm.with_structured_output(PuterPerplexityResponse)
        response = await structured_llm.ainvoke(prompt)

        if response and getattr(response, "sources", None):
            answer_by_source = {}
            citations = {}
            for i, source in enumerate(response.sources, 1):
                answer_by_source[i] = source.answer
                citations[i] = source.url

            full_answer_lines = []
            for i, source in enumerate(response.sources, 1):
                full_answer_lines.append(f"### [{i}]: {source.url}")
                full_answer_lines.append(source.answer)
                full_answer_lines.append("")
            full_answer = "\n".join(full_answer_lines)
            return full_answer, answer_by_source, citations
    except Exception as exc:
        logger.warning(f"Structured output failed with Puter AI, falling back to direct prompt: {exc}")

    # Fallback to direct invoke
    raw_response = await llm.ainvoke(prompt)
    content = raw_response.content if hasattr(raw_response, "content") else str(raw_response)
    if isinstance(content, list):
        content = "".join(str(part) for part in content)

    return parse_raw_puter_text(content)
