"""Core domain logic for code extraction, AST validation, subprocess sandboxing, and HTML publishing."""

import ast
import html
import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from ..utils.file_utils import read_file_safe
from ..utils.llm_utils import get_chat_model

logger = logging.getLogger(__name__)


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================


class ExtractedCodeSnippet(BaseModel):
    """Represents a code snippet extracted from markdown."""

    snippet_id: str
    language: str
    code: str
    line_estimate: int
    is_valid_syntax: bool = True
    syntax_error: Optional[str] = None
    target_filename: str


class CodeExtractionReport(BaseModel):
    """Summary of all extracted code blocks."""

    total_blocks_found: int
    languages_found: List[str]
    valid_syntax_count: int
    invalid_syntax_count: int
    snippets: List[ExtractedCodeSnippet]


class ExecutionResult(BaseModel):
    """Result of sandboxed execution."""

    snippet_id: str
    filename: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    success: bool


# ============================================================================
# CODE EXTRACTION & AST VALIDATION
# ============================================================================


def extract_code_blocks_from_markdown(markdown_text: str) -> List[ExtractedCodeSnippet]:
    """
    Extract fenced code blocks (```lang ... ```) from markdown text.
    """
    pattern = re.compile(r"```([a-zA-Z0-9_-]*)\n(.*?)```", re.DOTALL)
    matches = pattern.findall(markdown_text)

    snippets: List[ExtractedCodeSnippet] = []
    for idx, (lang, raw_code) in enumerate(matches, start=1):
        lang = lang.strip().lower() or "text"
        code = raw_code.strip()

        is_valid = True
        syntax_err = None

        if lang in ["python", "py"]:
            is_valid, syntax_err = validate_python_syntax(code)
            ext = "py"
        elif lang in ["json"]:
            is_valid, syntax_err = validate_json_syntax(code)
            ext = "json"
        elif lang in ["javascript", "js"]:
            ext = "js"
        elif lang in ["bash", "sh", "shell"]:
            ext = "sh"
        else:
            ext = "txt"

        filename = f"snippet_{idx}_{lang}.{ext}"

        snippets.append(
            ExtractedCodeSnippet(
                snippet_id=f"snippet_{idx}",
                language=lang,
                code=code,
                line_estimate=len(code.splitlines()),
                is_valid_syntax=is_valid,
                syntax_error=syntax_err,
                target_filename=filename,
            )
        )

    return snippets


def validate_python_syntax(code: str) -> Tuple[bool, Optional[str]]:
    """Validate Python code syntax using AST parser."""
    try:
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, f"SyntaxError at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, str(e)


def validate_json_syntax(code: str) -> Tuple[bool, Optional[str]]:
    """Validate JSON string syntax."""
    try:
        json.loads(code)
        return True, None
    except Exception as e:
        return False, f"JSONDecodeError: {e}"


# ============================================================================
# SUBPROCESS SANDBOX EXECUTION
# ============================================================================


def execute_python_in_sandbox(
    file_path: Path,
    timeout_seconds: int = 5,
) -> ExecutionResult:
    """
    Execute a Python file in an isolated subprocess with strict timeouts.
    """
    import time

    start_time = time.time()
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    try:
        proc = subprocess.run(
            [sys.executable, str(file_path)],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env=env,
        )
        duration_ms = (time.time() - start_time) * 1000
        return ExecutionResult(
            snippet_id=file_path.stem,
            filename=file_path.name,
            exit_code=proc.returncode,
            stdout=proc.stdout[:2000],
            stderr=proc.stderr[:2000],
            duration_ms=round(duration_ms, 2),
            success=(proc.returncode == 0),
        )
    except subprocess.TimeoutExpired:
        duration_ms = (time.time() - start_time) * 1000
        return ExecutionResult(
            snippet_id=file_path.stem,
            filename=file_path.name,
            exit_code=-1,
            stdout="",
            stderr=f"Execution timed out after {timeout_seconds} seconds.",
            duration_ms=round(duration_ms, 2),
            success=False,
        )
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        return ExecutionResult(
            snippet_id=file_path.stem,
            filename=file_path.name,
            exit_code=-1,
            stdout="",
            stderr=f"Execution failed: {e}",
            duration_ms=round(duration_ms, 2),
            success=False,
        )


# ============================================================================
# SELF-HEALING CODE REPAIR
# ============================================================================


async def repair_code_snippet_handler(
    broken_code: str,
    error_message: str,
    language: str = "python",
    model_name: str = "llama-3.1-8b",
) -> str:
    """
    Auto-repair broken code using LLM self-reflection.
    """
    prompt = f"""You are an elite software engineer and code repair specialist.
Fix the syntax or runtime error in the following {language} code snippet.

### Broken Code:
```{language}
{broken_code}
```

### Error Message:
{error_message}

### Instructions:
1. Fix all syntax, import, or logical errors.
2. Return ONLY the corrected, clean code. Do not wrap in markdown or include conversational explanations.
"""
    chat_model = get_chat_model(model_name)
    response = await chat_model.ainvoke(prompt)
    content = response.content if hasattr(response, "content") else str(response)

    # Clean out any backticks if returned
    clean_code = re.sub(r"^```[a-zA-Z]*\n", "", content)
    clean_code = re.sub(r"\n```$", "", clean_code)
    return clean_code.strip()


# ============================================================================
# HTML PUBLICATION COMPILER
# ============================================================================


def compile_markdown_to_html(markdown_text: str, title: str = "Maxy Publication Article") -> str:
    """
    Compile markdown text into a responsive, modern dark-mode HTML document.
    """
    escaped_title = html.escape(title)

    # Basic markdown transforms
    html_body = markdown_text

    # Code blocks
    html_body = re.sub(
        r"```([a-zA-Z0-9_-]*)\n(.*?)```",
        lambda m: f'<div class="code-container"><div class="code-header"><span class="code-lang">{m.group(1) or "code"}</span><button class="copy-btn" onclick="navigator.clipboard.writeText(this.parentElement.nextElementSibling.innerText)">Copy</button></div><pre><code>{html.escape(m.group(2).strip())}</code></pre></div>',
        html_body,
        flags=re.DOTALL,
    )

    # Inline code
    html_body = re.sub(r"`([^`]+)`", r"<code>\1</code>", html_body)

    # Headers
    html_body = re.sub(r"^# (.*?)$", r"<h1>\1</h1>", html_body, flags=re.MULTILINE)
    html_body = re.sub(r"^## (.*?)$", r"<h2>\1</h2>", html_body, flags=re.MULTILINE)
    html_body = re.sub(r"^### (.*?)$", r"<h3>\1</h3>", html_body, flags=re.MULTILINE)

    # Bold & Italic
    html_body = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", html_body)
    html_body = re.sub(r"\*(.*?)\*", r"<em>\1</em>", html_body)

    # Callouts
    html_body = re.sub(
        r"> \[!TIP\]\s*(.*?)(?=\n\n|\Z)",
        r'<div class="callout tip"><strong>💡 TIP:</strong> \1</div>',
        html_body,
        flags=re.DOTALL,
    )
    html_body = re.sub(
        r"> \[!NOTE\]\s*(.*?)(?=\n\n|\Z)",
        r'<div class="callout note"><strong>📌 NOTE:</strong> \1</div>',
        html_body,
        flags=re.DOTALL,
    )

    # Paragraphs (lines separated by double newlines)
    paragraphs = html_body.split("\n\n")
    formatted_paras = []
    for p in paragraphs:
        p_str = p.strip()
        if p_str.startswith("<h") or p_str.startswith("<div") or p_str.startswith("<pre") or p_str.startswith("<table"):
            formatted_paras.append(p_str)
        elif p_str.startswith("* ") or p_str.startswith("- "):
            items = "".join([f"<li>{item[2:].strip()}</li>" for item in p_str.splitlines() if item.strip()])
            formatted_paras.append(f"<ul>{items}</ul>")
        else:
            formatted_paras.append(f"<p>{p_str}</p>")

    final_content = "\n".join(formatted_paras)

    template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escaped_title}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-primary: #0a0d14;
            --bg-surface: #111726;
            --bg-code: #161f33;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --accent-cyan: #06b6d4;
            --accent-purple: #8b5cf6;
            --accent-green: #10b981;
            --border-subtle: rgba(255, 255, 255, 0.08);
            --font-main: 'Inter', -apple-system, sans-serif;
            --font-code: 'JetBrains Mono', monospace;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background-color: var(--bg-primary);
            color: var(--text-primary);
            font-family: var(--font-main);
            line-height: 1.7;
            padding: 2.5rem 1.5rem;
            display: flex;
            justify-content: center;
        }}
        .article-wrapper {{
            max-width: 860px;
            width: 100%;
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: 16px;
            padding: 3.5rem;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }}
        .badge-bar {{
            display: flex;
            gap: 0.5rem;
            margin-bottom: 2rem;
        }}
        .badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            font-size: 0.75rem;
            font-weight: 600;
            border-radius: 9999px;
            background: rgba(6, 182, 212, 0.15);
            color: var(--accent-cyan);
            border: 1px solid rgba(6, 182, 212, 0.3);
        }}
        h1 {{
            font-size: 2.4rem;
            font-weight: 800;
            background: linear-gradient(135deg, #38bdf8 0%, #c084fc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 1.5rem;
            letter-spacing: -0.025em;
        }}
        h2 {{
            font-size: 1.6rem;
            font-weight: 700;
            color: #e2e8f0;
            margin-top: 2.5rem;
            margin-bottom: 1rem;
            border-bottom: 1px solid var(--border-subtle);
            padding-bottom: 0.5rem;
        }}
        h3 {{
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--accent-cyan);
            margin-top: 1.75rem;
            margin-bottom: 0.75rem;
        }}
        p {{
            margin-bottom: 1.25rem;
            color: var(--text-secondary);
            font-size: 1.05rem;
        }}
        ul {{
            margin-left: 1.5rem;
            margin-bottom: 1.5rem;
            color: var(--text-secondary);
        }}
        li {{ margin-bottom: 0.5rem; }}
        .code-container {{
            background: var(--bg-code);
            border: 1px solid var(--border-subtle);
            border-radius: 10px;
            margin: 1.75rem 0;
            overflow: hidden;
        }}
        .code-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.5rem 1rem;
            background: rgba(255, 255, 255, 0.03);
            border-bottom: 1px solid var(--border-subtle);
        }}
        .code-lang {{
            font-family: var(--font-code);
            font-size: 0.75rem;
            text-transform: uppercase;
            color: var(--accent-cyan);
            font-weight: 700;
        }}
        .copy-btn {{
            background: transparent;
            border: 1px solid var(--border-subtle);
            color: var(--text-secondary);
            font-size: 0.75rem;
            padding: 0.2rem 0.6rem;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .copy-btn:hover {{
            background: var(--accent-cyan);
            color: #000;
        }}
        pre {{
            padding: 1.25rem;
            overflow-x: auto;
            font-family: var(--font-code);
            font-size: 0.9rem;
            color: #e2e8f0;
        }}
        code {{
            font-family: var(--font-code);
            background: rgba(255, 255, 255, 0.08);
            padding: 0.15rem 0.4rem;
            border-radius: 4px;
            font-size: 0.9em;
            color: #38bdf8;
        }}
        .callout {{
            padding: 1rem 1.25rem;
            border-radius: 8px;
            margin: 1.5rem 0;
            font-size: 0.95rem;
        }}
        .callout.tip {{
            background: rgba(16, 185, 129, 0.1);
            border-left: 4px solid var(--accent-green);
            color: #a7f3d0;
        }}
        .callout.note {{
            background: rgba(139, 92, 246, 0.1);
            border-left: 4px solid var(--accent-purple);
            color: #ddd6fe;
        }}
        footer {{
            margin-top: 3rem;
            padding-top: 1.5rem;
            border-top: 1px solid var(--border-subtle);
            text-align: center;
            font-size: 0.85rem;
            color: #64748b;
        }}
    </style>
</head>
<body>
    <div class="article-wrapper">
        <div class="badge-bar">
            <span class="badge">🚀 Verified Code</span>
            <span class="badge">⚡ Model Context Protocol</span>
            <span class="badge">✍️ Maxy Publisher</span>
        </div>
        {final_content}
        <footer>
            Published autonomously by <strong>Maxy AI Research & Publishing Engine</strong> • Powered by FastMCP & Comet Opik
        </footer>
    </div>
</body>
</html>
"""
    return template
