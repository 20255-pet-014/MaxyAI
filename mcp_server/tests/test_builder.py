"""Tests for the Maxy Code Sandbox Evaluator and Publisher tools (Phase 3)."""

import tempfile
import unittest
from pathlib import Path

from src.app.builder_handler import (
    compile_markdown_to_html,
    execute_python_in_sandbox,
    extract_code_blocks_from_markdown,
    validate_json_syntax,
    validate_python_syntax,
)
from src.tools.builder_tools import (
    execute_sandbox_tests_tool,
    export_publication_bundle_tool,
    extract_and_validate_code_tool,
)


class BuilderUnitTests(unittest.TestCase):
    """Test AST parsing, code block extraction, and HTML compilation."""

    def test_extract_code_blocks(self):
        markdown = """# Sample Article
Here is python code:
```python
def add(a, b):
    return a + b
```
And some JSON:
```json
{
  "key": "value"
}
```
"""
        snippets = extract_code_blocks_from_markdown(markdown)
        self.assertEqual(len(snippets), 2)
        self.assertEqual(snippets[0].language, "python")
        self.assertTrue(snippets[0].is_valid_syntax)
        self.assertEqual(snippets[1].language, "json")
        self.assertTrue(snippets[1].is_valid_syntax)

    def test_validate_python_syntax(self):
        valid_code = "x = [1, 2, 3]\nprint(sum(x))"
        is_val, err = validate_python_syntax(valid_code)
        self.assertTrue(is_val)
        self.assertIsNone(err)

        invalid_code = "def broken(:\n    pass"
        is_val, err = validate_python_syntax(invalid_code)
        self.assertFalse(is_val)
        self.assertIsNotNone(err)

    def test_validate_json_syntax(self):
        valid_json = '{"status": "ok", "count": 42}'
        is_val, err = validate_json_syntax(valid_json)
        self.assertTrue(is_val)

        invalid_json = '{"status": "ok",}'
        is_val, err = validate_json_syntax(invalid_json)
        self.assertFalse(is_val)

    def test_execute_python_in_sandbox(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            py_file = Path(tmp_dir) / "test_script.py"
            py_file.write_text("print('Hello from sandbox!')", encoding="utf-8")

            res = execute_python_in_sandbox(py_file, timeout_seconds=3)
            self.assertTrue(res.success)
            self.assertEqual(res.exit_code, 0)
            self.assertIn("Hello from sandbox!", res.stdout)

    def test_compile_markdown_to_html(self):
        md = "# Main Title\n\nThis is a paragraph with `inline code`.\n\n```python\nprint('demo')\n```"
        html_out = compile_markdown_to_html(md, title="Test Article")
        self.assertIn("<title>Test Article</title>", html_out)
        self.assertIn("<h1>Main Title</h1>", html_out)
        self.assertIn("<code>inline code</code>", html_out)
        self.assertIn("print(", html_out)
        self.assertIn("article-wrapper", html_out)


class BuilderAsyncToolTests(unittest.IsolatedAsyncioTestCase):
    """Test asynchronous Builder tools."""

    async def test_extract_and_validate_code_tool(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            article_content = "# Title\n```python\nx = 10\n```\n"
            (tmp_path / "article.md").write_text(article_content, encoding="utf-8")

            res = await extract_and_validate_code_tool(str(tmp_path))
            self.assertEqual(res["status"], "success")
            self.assertEqual(res["total_snippets"], 1)
            self.assertEqual(res["valid_syntax_count"], 1)

            sandbox_files = list((tmp_path / ".nova" / "sandbox").glob("*.py"))
            self.assertEqual(len(sandbox_files), 1)

    async def test_execute_sandbox_tests_tool(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            sandbox_dir = tmp_path / ".nova" / "sandbox"
            sandbox_dir.mkdir(parents=True)
            (sandbox_dir / "snippet_1_python.py").write_text("print('Passed')", encoding="utf-8")

            res = await execute_sandbox_tests_tool(str(tmp_path))
            self.assertEqual(res["status"], "success")
            self.assertEqual(res["passed"], 1)
            self.assertEqual(res["failed"], 0)

    async def test_export_publication_bundle_tool(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            (tmp_path / "article.md").write_text("# Published Article\nContent here.", encoding="utf-8")

            res = await export_publication_bundle_tool(str(tmp_path), article_title="My Publication")
            self.assertEqual(res["status"], "success")
            html_file = tmp_path / "article.html"
            self.assertTrue(html_file.exists())
            self.assertGreater(res["size_bytes"], 100)
