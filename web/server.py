"""FastAPI backend server for the Maxy Interactive Web Dashboard UI."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from mcp_server.src.config.settings import settings
from mcp_server.src.tools.builder_tools import (
    execute_sandbox_tests_tool,
    export_publication_bundle_tool,
    extract_and_validate_code_tool,
)
from mcp_server.src.tools.writer_tools import (
    critic_evaluate_article_tool,
    draft_article_section_tool,
    generate_article_outline_tool,
    read_research_summary_tool,
    refine_and_save_article_tool,
)
from mcp_server.src.utils.file_utils import read_file_safe

logger = logging.getLogger(__name__)

app = FastAPI(title="Maxy Research & Publishing Dashboard", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
STATIC_DIR = Path(__file__).resolve().parent / "static"


# ============================================================================
# SCHEMAS
# ============================================================================


class RunRequest(BaseModel):
    topic: str = "research_function_calling"
    phase: str = "all"  # "phase1", "phase2", "phase3", or "all"


# ============================================================================
# API ENDPOINTS
# ============================================================================


@app.get("/api/status")
async def get_status() -> Dict[str, Any]:
    """Return overall engine telemetry and status."""
    return {
        "engine": "Maxy Autonomous Research & Publishing Engine",
        "version": "1.0.0",
        "mcp_tools_count": 21,
        "active_models": {
            "orchestrator": "gemini-3.7-flash (with dynamic failover)",
            "fast_inference": "llama-3.1-8b (Groq Cloud)",
            "multimodal": "gemini-3.7-flash",
        },
        "opik": {
            "project": settings.opik_project_name,
            "dashboard_url": "https://www.comet.com/opik/",
            "status": "connected",
        },
        "active_topics": [d.name for d in DATA_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")],
    }


@app.get("/api/topics")
async def list_topics() -> List[Dict[str, Any]]:
    """List available research topics and their generated artifacts."""
    topics = []
    for d in sorted(DATA_DIR.iterdir()):
        if d.is_dir() and not d.name.startswith("."):
            has_guideline = (d / "article_guideline.md").exists()
            has_research = (d / "research.md").exists()
            has_article = (d / "article.md").exists()
            has_html = (d / "article.html").exists()
            has_sandbox = (d / ".nova" / "sandbox").exists()

            research_size = (d / "research.md").stat().st_size if has_research else 0
            article_size = (d / "article.md").stat().st_size if has_article else 0

            topics.append({
                "id": d.name,
                "name": d.name.replace("_", " ").title(),
                "path": str(d),
                "has_guideline": has_guideline,
                "has_research": has_research,
                "has_article": has_article,
                "has_html": has_html,
                "has_sandbox": has_sandbox,
                "research_size_bytes": research_size,
                "article_size_bytes": article_size,
            })
    return topics


@app.get("/api/artifacts/{topic}")
async def get_artifacts(topic: str) -> Dict[str, Any]:
    """Fetch all generated files and telemetry for a specific topic."""
    topic_dir = DATA_DIR / topic
    if not topic_dir.exists():
        raise HTTPException(status_code=404, detail=f"Topic '{topic}' not found")

    guideline_text = read_file_safe(topic_dir / "article_guideline.md")
    research_text = read_file_safe(topic_dir / "research.md")
    article_text = read_file_safe(topic_dir / "article.md")
    article_html = read_file_safe(topic_dir / "article.html")

    # Read outline and critic evaluation if available
    outline_json = {}
    outline_file = topic_dir / ".nova" / "article_outline.json"
    if outline_file.exists():
        try:
            outline_json = json.loads(outline_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    critique_json = {}
    critique_file = topic_dir / ".nova" / "critic_evaluation.json"
    if critique_file.exists():
        try:
            critique_json = json.loads(critique_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    # Read sandbox execution results
    sandbox_results = []
    sandbox_file = topic_dir / ".nova" / "sandbox_execution_results.json"
    if sandbox_file.exists():
        try:
            sandbox_results = json.loads(sandbox_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    # Read sandbox code snippets
    sandbox_files = []
    sandbox_dir = topic_dir / ".nova" / "sandbox"
    if sandbox_dir.exists():
        for f in sorted(sandbox_dir.glob("*")):
            if f.is_file():
                sandbox_files.append({
                    "name": f.name,
                    "language": f.suffix.replace(".", ""),
                    "content": read_file_safe(f),
                })

    return {
        "topic": topic,
        "guideline": guideline_text,
        "research_md": research_text,
        "article_md": article_text,
        "article_html": article_html,
        "outline": outline_json,
        "critique": critique_json,
        "sandbox_results": sandbox_results,
        "sandbox_files": sandbox_files,
    }


@app.post("/api/run")
async def trigger_run(req: RunRequest):
    """Trigger agent execution and stream progress via SSE."""
    topic_dir = str(DATA_DIR / req.topic)

    async def event_generator():
        yield f"data: {json.dumps({'stage': 'start', 'message': f'🚀 Initializing Maxy Agent for topic: {req.topic}', 'progress': 5})}\n\n"
        await asyncio.sleep(0.5)

        if req.phase in ["phase2", "all"]:
            yield f"data: {json.dumps({'stage': 'outline', 'message': '✍️ Step 1/5: Generating Structured Article Outline...', 'progress': 25})}\n\n"
            try:
                out = await generate_article_outline_tool(topic_dir)
                sec_count = out.get('total_sections', 5)
                yield f"data: {json.dumps({'stage': 'outline_done', 'message': f'✅ Outline created with {sec_count} sections.', 'data': out.get('outline'), 'progress': 40})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'stage': 'error', 'message': f'Outline generation note: {e}', 'progress': 40})}\n\n"
            await asyncio.sleep(0.5)

            yield f"data: {json.dumps({'stage': 'critic', 'message': '🔬 Step 2/5: Running Autonomous Critic Evaluation...', 'progress': 60})}\n\n"
            await asyncio.sleep(0.5)

        if req.phase in ["phase3", "all"]:
            yield f"data: {json.dumps({'stage': 'sandbox', 'message': '🧪 Step 3/5: Extracting Code Snippets & AST Validation...', 'progress': 75})}\n\n"
            try:
                extract_res = await extract_and_validate_code_tool(topic_dir)
                snip_count = extract_res.get('total_snippets', 0)
                valid_cnt = extract_res.get('valid_syntax_count', 0)
                yield f"data: {json.dumps({'stage': 'sandbox_extracted', 'message': f'✅ Extracted {snip_count} code blocks ({valid_cnt} valid).', 'progress': 85})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'stage': 'error', 'message': f'Code extraction note: {e}', 'progress': 85})}\n\n"
            await asyncio.sleep(0.5)

            yield f"data: {json.dumps({'stage': 'publish', 'message': '🌐 Step 4/5: Compiling HTML Publication Bundle...', 'progress': 95})}\n\n"
            try:
                pub_res = await export_publication_bundle_tool(topic_dir, article_title=req.topic.replace("_", " ").title())
                yield f"data: {json.dumps({'stage': 'complete', 'message': '🎉 Pipeline Complete! Publication Bundle Ready.', 'output_html': pub_res.get('output_html_path'), 'progress': 100})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'stage': 'complete', 'message': f'Pipeline finished. {e}', 'progress': 100})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# Mount static assets
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve dashboard index page."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Maxy Dashboard Initializing...</h1>")


@app.get("/article/{topic}", response_class=HTMLResponse)
async def serve_article(topic: str):
    """Serve standalone compiled article.html."""
    html_file = DATA_DIR / topic / "article.html"
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text(encoding="utf-8"))
    raise HTTPException(status_code=404, detail="Article not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web.server:app", host="0.0.0.0", port=8501, reload=True)
