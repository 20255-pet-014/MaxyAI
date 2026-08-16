"""FastMCP tool implementations for the Maxy Code Sandbox Evaluator & Publisher Agent (Phase 3)."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..app.builder_handler import (
    compile_markdown_to_html,
    execute_python_in_sandbox,
    extract_code_blocks_from_markdown,
    repair_code_snippet_handler,
)
from ..config.settings import settings
from ..utils.file_utils import read_file_safe, validate_research_folder

logger = logging.getLogger(__name__)


# ============================================================================
# TOOL 1: EXTRACT AND VALIDATE CODE
# ============================================================================


async def extract_and_validate_code_tool(research_directory: str) -> Dict[str, Any]:
    """
    Extract all code blocks from article.md, validate their AST syntax, and store in .nova/sandbox/.

    Args:
        research_directory: The absolute path to the research directory

    Returns:
        Dict containing counts of valid and invalid code blocks, list of snippets, and sandbox location.
    """
    path = Path(research_directory)
    validate_research_folder(path)

    article_path = path / "article.md"
    if not article_path.exists():
        raise ValueError(f"No article.md found in '{path}'. Please run the Writer Agent first.")

    article_text = read_file_safe(article_path)
    snippets = extract_code_blocks_from_markdown(article_text)

    sandbox_dir = path / ".nova" / "sandbox"
    sandbox_dir.mkdir(exist_ok=True, parents=True)

    # Save snippets to sandbox directory
    valid_count = 0
    invalid_count = 0
    saved_files = []

    for snip in snippets:
        file_dest = sandbox_dir / snip.target_filename
        file_dest.write_text(snip.code, encoding="utf-8")
        saved_files.append(str(file_dest))
        if snip.is_valid_syntax:
            valid_count += 1
        else:
            invalid_count += 1

    # Save extraction manifest to .nova/sandbox_manifest.json
    manifest_path = path / ".nova" / "sandbox_manifest.json"
    manifest_data = {
        "total_snippets": len(snippets),
        "valid_syntax_count": valid_count,
        "invalid_syntax_count": invalid_count,
        "snippets": [s.model_dump() for s in snippets],
    }
    manifest_path.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

    return {
        "status": "success",
        "total_snippets": len(snippets),
        "valid_syntax_count": valid_count,
        "invalid_syntax_count": invalid_count,
        "sandbox_directory": str(sandbox_dir),
        "manifest_path": str(manifest_path),
        "message": f"Extracted {len(snippets)} code blocks ({valid_count} valid, {invalid_count} syntax errors). Saved to '{sandbox_dir}'.",
    }


# ============================================================================
# TOOL 2: EXECUTE SANDBOX TESTS
# ============================================================================


async def execute_sandbox_tests_tool(research_directory: str) -> Dict[str, Any]:
    """
    Execute all extracted Python code snippets in an isolated subprocess sandbox.

    Args:
        research_directory: The absolute path to the research directory

    Returns:
        Dict containing execution results, pass/fail counts, and outputs.
    """
    path = Path(research_directory)
    validate_research_folder(path)

    sandbox_dir = path / ".nova" / "sandbox"
    if not sandbox_dir.exists():
        raise ValueError(f"No sandbox folder found at '{sandbox_dir}'. Please run extract_and_validate_code first.")

    python_files = list(sandbox_dir.glob("*.py"))
    if not python_files:
        return {
            "status": "success",
            "message": "No Python files found in sandbox to execute.",
            "total_tested": 0,
            "passed": 0,
            "failed": 0,
            "results": [],
        }

    results = []
    passed = 0
    failed = 0

    for py_file in python_files:
        res = execute_python_in_sandbox(py_file, timeout_seconds=5)
        results.append(res.model_dump())
        if res.success:
            passed += 1
        else:
            failed += 1

    # Save results to .nova/sandbox_execution_results.json
    results_path = path / ".nova" / "sandbox_execution_results.json"
    results_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    return {
        "status": "success",
        "total_tested": len(python_files),
        "passed": passed,
        "failed": failed,
        "results": results,
        "saved_path": str(results_path),
        "message": f"Executed {len(python_files)} Python snippets: {passed} passed, {failed} failed.",
    }


# ============================================================================
# TOOL 3: FIX CODE SNIPPETS
# ============================================================================


async def fix_code_snippets_tool(
    research_directory: str,
    broken_code: str,
    error_message: str,
    language: str = "python",
) -> Dict[str, Any]:
    """
    Automatically repair broken code snippets using LLM self-reflection.

    Args:
        research_directory: The absolute path to the research directory
        broken_code: The raw code string that caused a syntax or runtime failure
        error_message: The traceback or error message
        language: Programming language (default: python)

    Returns:
        Dict containing corrected code and syntax validation status.
    """
    path = Path(research_directory)
    validate_research_folder(path)

    repaired_code = await repair_code_snippet_handler(
        broken_code=broken_code,
        error_message=error_message,
        language=language,
        model_name=settings.scraping_model,
    )

    is_valid = True
    syntax_err = None
    if language in ["python", "py"]:
        from ..app.builder_handler import validate_python_syntax
        is_valid, syntax_err = validate_python_syntax(repaired_code)

    return {
        "status": "success",
        "is_valid_syntax": is_valid,
        "syntax_error": syntax_err,
        "repaired_code": repaired_code,
        "message": "Successfully repaired code snippet using self-healing LLM reflection.",
    }


# ============================================================================
# TOOL 4: EXPORT PUBLICATION BUNDLE
# ============================================================================


async def export_publication_bundle_tool(
    research_directory: str,
    article_title: str = "Maxy Technical Article",
) -> Dict[str, Any]:
    """
    Compile verified markdown article into a responsive, standalone HTML publication document (article.html).

    Args:
        research_directory: The absolute path to the research directory
        article_title: The title of the article document

    Returns:
        Dict confirming output HTML path, file size, and publication status.
    """
    path = Path(research_directory)
    validate_research_folder(path)

    article_path = path / "article.md"
    if not article_path.exists():
        raise ValueError(f"No article.md found in '{path}'. Please run Writer Agent first.")

    article_md = read_file_safe(article_path)
    html_content = compile_markdown_to_html(article_md, title=article_title)

    output_html_path = path / "article.html"
    output_html_path.write_text(html_content, encoding="utf-8")

    size_bytes = len(html_content.encode("utf-8"))

    return {
        "status": "success",
        "output_html_path": str(output_html_path),
        "size_bytes": size_bytes,
        "message": f"Successfully compiled publication bundle to '{output_html_path}' ({size_bytes} bytes).",
    }
