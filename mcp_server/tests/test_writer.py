"""Tests for the Maxy Writer and Critic tools."""

import asyncio
import json
import unittest
from pathlib import Path
import tempfile

from src.app.writer_handler import (
    ArticleOutline,
    ArticleSectionOutline,
    CriticEvaluation,
    extract_research_metadata,
)
from src.tools.writer_tools import (
    read_research_summary_tool,
    refine_and_save_article_tool,
)


class WriterSchemaTests(unittest.TestCase):
    """Test schemas and synchronous utilities."""

    def test_pydantic_schemas(self):
        """Verify ArticleOutline and CriticEvaluation schema validation."""
        section = ArticleSectionOutline(
            section_id="sec_1",
            title="Introduction to AsyncIO",
            key_points=["Event loop fundamentals", "Async/await syntax"],
            target_word_count=300,
            include_code=True,
            citations_to_reference=["https://docs.python.org"],
        )
        outline = ArticleOutline(
            title="Mastering Modern Async Python",
            subtitle="Architecting resilient concurrent systems",
            target_audience="Senior Python Engineers",
            estimated_read_time_minutes=10,
            sections=[section],
        )
        self.assertEqual(outline.title, "Mastering Modern Async Python")
        self.assertEqual(len(outline.sections), 1)
        self.assertTrue(outline.sections[0].include_code)

        critique = CriticEvaluation(
            overall_score=92,
            strengths=["Deep technical explanations", "Clear code samples"],
            areas_for_improvement=["Add error handling section"],
            factual_citation_check="All citations valid",
            code_quality_check="Syntactically correct Python",
            actionable_revisions=["Include retry backoff code"],
        )
        self.assertEqual(critique.overall_score, 92)
        self.assertEqual(len(critique.strengths), 2)

    def test_extract_research_metadata(self):
        """Test extracting metadata from research.md."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "article_guideline.md").write_text("# Guidelines\nWrite about Python async patterns with code samples.", encoding="utf-8")
            (temp_path / "research.md").write_text("# Research\nSource [1]: https://docs.python.org\nSource [2]: https://github.com/python", encoding="utf-8")
            
            meta = extract_research_metadata(temp_path)
            self.assertIn("Guidelines", meta["guidelines"])
            self.assertGreaterEqual(meta["total_sources_cited"], 2)


class WriterAsyncToolTests(unittest.IsolatedAsyncioTestCase):
    """Test asynchronous Writer tools."""

    async def test_read_research_summary_tool(self):
        """Test read_research_summary_tool."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "article_guideline.md").write_text("# Guidelines\nTest content", encoding="utf-8")
            (temp_path / "research.md").write_text("# Research\nSource [1]: https://docs.python.org", encoding="utf-8")

            res = await read_research_summary_tool(str(temp_path))
            self.assertEqual(res["status"], "success")
            self.assertGreaterEqual(res["total_sources_cited"], 1)

    async def test_refine_and_save_article_tool(self):
        """Test refine_and_save_article_tool writing article.md."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "article_guideline.md").write_text("# Guidelines", encoding="utf-8")

            # Mock refine_article_handler
            async def mock_refine(article_text, critic_feedback, model_name):
                return f"# Refined Article\n\n{article_text}\n\n## References\n- Source 1"

            import unittest.mock as mock
            with mock.patch("src.tools.writer_tools.refine_article_handler", side_effect=mock_refine):
                draft = "## Overview\nThis is a sample article draft."
                res = await refine_and_save_article_tool(
                    research_directory=str(temp_path),
                    article_content=draft,
                    critic_feedback=["Add TOC", "Polish code"],
                )
                self.assertEqual(res["status"], "success")
                article_file = temp_path / "article.md"
                self.assertTrue(article_file.exists())
                content = article_file.read_text(encoding="utf-8")
                self.assertIn("# Refined Article", content)
