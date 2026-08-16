"""LLM utilities for configuration and response processing (Gemini, Groq, OpenAI)."""

import json
import logging
from typing import Any, List, Optional

from openai import AsyncOpenAI
from google import genai
from google.genai import types

from ..settings import settings
from .opik_handler import track_genai_client

logger = logging.getLogger(__name__)


class OpenAIResponseCandidate:
    def __init__(self, content):
        self.content = content


class OpenAIResponseContent:
    def __init__(self, parts, role="model"):
        self.parts = parts
        self.role = role


class OpenAIResponsePart:
    def __init__(self, text=None, thought=False, function_call=None):
        self.text = text
        self.thought = thought
        self.function_call = function_call


class OpenAIFunctionCall:
    def __init__(self, name, args):
        self.name = name
        self.args = args


class OpenAIResponseAdapter:
    def __init__(self, raw_message):
        self.raw_message = raw_message
        self.function_calls = []
        parts = []

        if getattr(raw_message, "tool_calls", None) and raw_message.tool_calls:
            for tc in raw_message.tool_calls:
                fn_name = tc.function.name
                try:
                    fn_args = json.loads(tc.function.arguments) if isinstance(tc.function.arguments, str) else tc.function.arguments
                except Exception:
                    fn_args = {}
                fc_obj = OpenAIFunctionCall(name=fn_name, args=fn_args)
                self.function_calls.append(fc_obj)
                parts.append(OpenAIResponsePart(function_call=fc_obj))

        content_text = getattr(raw_message, "content", None)
        if content_text:
            parts.append(OpenAIResponsePart(text=content_text, thought=False))

        # Check for reasoning/thinking
        reasoning = getattr(raw_message, "reasoning", None) or getattr(raw_message, "reasoning_content", None)
        if reasoning:
            parts.insert(0, OpenAIResponsePart(text=reasoning, thought=True))

        content_obj = OpenAIResponseContent(parts=parts, role="model")
        self.candidates = [OpenAIResponseCandidate(content=content_obj)]


def build_llm_config_with_tools(mcp_tools: List, thinking_enabled: bool = True, model_id: Optional[str] = None) -> Any:
    """Build LLM config with all MCP tools converted to target format."""
    target_model = model_id or settings.model_id
    if target_model.startswith("gemini"):
        gemini_tools = []
        for tool in mcp_tools:
            gemini_tool = types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name=tool.name,
                        description=tool.description,
                        parameters=tool.inputSchema,
                    )
                ]
            )
            gemini_tools.append(gemini_tool)

        if settings.thinking_level is not None:
            thinking_config = types.ThinkingConfig(
                include_thoughts=thinking_enabled,
                thinking_level=settings.thinking_level,
            )
        else:
            thinking_config = types.ThinkingConfig(
                include_thoughts=thinking_enabled,
                thinking_budget=settings.thinking_budget,
            )

        return types.GenerateContentConfig(
            tools=gemini_tools,
            thinking_config=thinking_config,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
    else:
        openai_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema or {},
                },
            }
            for tool in mcp_tools
        ]
        return {"tools": openai_tools}


def extract_thought_summary(response: Any) -> str | None:
    """Collect human-readable thought summaries if present."""
    if not getattr(response, "candidates", None):
        return None
    parts = getattr(response.candidates[0].content, "parts", []) or []
    chunks = [p.text for p in parts if getattr(p, "thought", False) and getattr(p, "text", None)]
    return "\n".join(chunks).strip() if chunks else None


def extract_final_answer(response: Any) -> str | None:
    """Extract the final answer from the response."""
    if not getattr(response, "candidates", None):
        return None
    parts = getattr(response.candidates[0].content, "parts", []) or []
    chunks = [p.text for p in parts if not getattr(p, "thought", False) and getattr(p, "text", None)]
    return "\n".join(chunks).strip() if chunks else None


def extract_first_function_call(response: Any):
    """Return (name, args) for the first function call, or None if the model produced a final answer."""
    if getattr(response, "function_calls", None) and response.function_calls:
        fc = response.function_calls[0]
        return fc.name, dict(fc.args or {})
    if not getattr(response, "candidates", None):
        return None
    parts = getattr(response.candidates[0].content, "parts", []) or []
    for p in parts:
        if getattr(p, "function_call", None):
            fc = p.function_call
            return fc.name, dict(fc.args or {})
    return None


class LLMClient:
    """Model-agnostic LLM client for generating content."""

    def __init__(self, model_id: str, llm_config: Any):
        self.model_id = model_id
        self.llm_config = llm_config
        self.is_gemini = model_id.startswith("gemini")

        if self.is_gemini:
            if not settings.google_api_key:
                raise RuntimeError("GOOGLE_API_KEY environment variable not set.")
            base_client = genai.Client(api_key=settings.google_api_key.get_secret_value())
            self.client = track_genai_client(base_client)
        else:
            config = settings.orchestrator_configs.get(model_id, {})
            identifier = config.get("identifier", "openai:llama-3.3-70b-versatile")
            self.openai_model_name = identifier.split(":", 1)[1] if ":" in identifier else identifier
            params = config.get("params", {})
            base_url = params.get("base_url", "https://api.groq.com/openai/v1")

            api_key = None
            if settings.groq_api_key:
                api_key = settings.groq_api_key.get_secret_value()
            elif settings.openai_api_key:
                api_key = settings.openai_api_key.get_secret_value()

            if not api_key:
                raise RuntimeError("GROQ_API_KEY environment variable not set.")

            self.openai_client = AsyncOpenAI(base_url=base_url, api_key=api_key)

    async def generate_content(self, contents: List[Any]) -> Any:
        """Generate content using the configured LLM model with automatic model failover on 429."""
        if self.is_gemini:
            import asyncio
            candidate_models = [self.model_id, "gemini-3.6-flash", "gemini-flash-lite-latest", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]
            # Deduplicate preserving order
            unique_models = []
            for m in candidate_models:
                if m not in unique_models:
                    unique_models.append(m)

            last_error = None
            for model_name in unique_models:
                try:
                    return await self.client.aio.models.generate_content(
                        model=model_name,
                        contents=contents,
                        config=self.llm_config,
                    )
                except Exception as e:
                    err_str = str(e)
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "503" in err_str:
                        logger.warning(f"Quota / rate limit reached on {model_name}. Failing over to next available model...")
                        print(f"\n🔄 Model quota reached on {model_name}. Automatically failing over to next available model...")
                        last_error = e
                        await asyncio.sleep(1)
                        continue
                    else:
                        raise e
            if last_error:
                raise last_error
        else:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are the Nova Research Agent. Follow the research workflow precisely.\n"
                        "Use the provided tools to perform web research, scraping, source selection, and report compilation.\n"
                        "Always invoke tools with valid JSON arguments using the exact user-provided research directory path.\n"
                        "Never output raw XML function tags like <function=...> in text. Always use native tool calling."
                    ),
                }
            ]
            for item in contents:
                if isinstance(item, dict):
                    messages.append(item)
                elif hasattr(item, "role") and hasattr(item, "parts"):
                    role = "assistant" if item.role == "model" else "user"
                    parts_text = []
                    for part in item.parts:
                        if getattr(part, "text", None):
                            parts_text.append(part.text)
                    if parts_text:
                        messages.append({"role": role, "content": "\n".join(parts_text)})
                else:
                    messages.append({"role": "user", "content": str(item)})

            tools = self.llm_config.get("tools") if isinstance(self.llm_config, dict) else None
            kwargs: dict[str, Any] = {
                "model": self.openai_model_name,
                "messages": messages,
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            res = await self.openai_client.chat.completions.create(**kwargs)
            return OpenAIResponseAdapter(res.choices[0].message)
