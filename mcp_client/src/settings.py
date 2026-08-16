"""Client configuration settings."""

import logging
from pathlib import Path
from typing import Any, Dict, Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

ThinkingLevel = Literal["minimal", "low", "medium", "high"]


class Settings(BaseSettings):
    """Application settings for the MCP Client."""

    model_config = SettingsConfigDict(
        env_file=(".env", "mcp_client/.env", "../mcp_client/.env", "mcp_server/.env", "../mcp_server/.env"),
        extra="ignore",
        env_file_encoding="utf-8",
    )

    # Server settings and paths
    project_root: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent, description="The root directory of the mcp_client project"
    )
    server_main_path: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent.parent / "mcp_server",
        description="The path to the server's main.py file",
    )
    log_level: int = Field(default=logging.INFO, alias="LOG_LEVEL", description="The log level")
    log_level_dependencies: int = Field(
        default=logging.WARNING, alias="LOG_LEVEL_DEPENDENCIES", description="The log level for dependencies"
    )

    # LLM Configuration
    orchestrator_key: str = Field(default="gemini-3.7-flash", description="Default orchestrator model key")
    model_id: str = Field(default="gemini-3.7-flash", description="Default model ID for LLM operations")
    thinking_budget: int | None = Field(
        default=None, description="Thinking token budget for Gemini 2.5 models. Mutually exclusive with thinking_level."
    )
    thinking_level: ThinkingLevel | None = Field(
        default="low", description="Reasoning depth for Gemini 3.x models. Mutually exclusive with thinking_budget."
    )
    thinking_enabled: bool = Field(default=True, description="Whether thinking is enabled by default")

    # Agent configuration
    recursion_limit: int = Field(default=100, description="The recursion limit for the agent")

    # API Keys
    groq_api_key: SecretStr | None = Field(default=None, alias="GROQ_API_KEY", description="The API key for Groq Cloud")
    google_api_key: SecretStr | None = Field(default=None, alias="GOOGLE_API_KEY", description="The API key for the Google API")
    openai_api_key: SecretStr | None = Field(default=None, alias="OPENAI_API_KEY", description="The API key for the OpenAI API")

    # Opik Configuration
    opik_api_key: SecretStr | None = Field(default=None, alias="OPIK_API_KEY", description="The API key for Opik")
    opik_workspace: str | None = Field(default=None, alias="OPIK_WORKSPACE", description="The Opik workspace name")
    opik_project_name: str = Field(default="maxy", alias="OPIK_PROJECT_NAME", description="The Opik project name")

    @model_validator(mode="after")
    def _check_thinking_exclusive(self) -> "Settings":
        if self.thinking_budget is not None and self.thinking_level is not None:
            raise ValueError("`thinking_budget` and `thinking_level` are mutually exclusive; set only one.")
        return self

    @property
    def orchestrator_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get the orchestrator configurations."""
        return {
            "gemini-3.7-flash": {
                "identifier": "google_genai:gemini-3.7-flash",
                "params": {
                    "temperature": 1,
                    "thinking_level": "low",
                    "include_thoughts": True,
                    "max_retries": 3,
                },
            },
            "gemini-3.5-flash": {
                "identifier": "google_genai:gemini-3.5-flash",
                "params": {
                    "temperature": 1,
                    "thinking_level": "low",
                    "include_thoughts": True,
                    "max_retries": 3,
                },
            },
            "llama-3.1-8b": {
                "identifier": "openai:llama-3.1-8b-instant",
                "api_key_env_var": "GROQ_API_KEY",
                "params": {
                    "base_url": "https://api.groq.com/openai/v1",
                    "temperature": 0.7,
                },
            },
            "llama-3.3-70b": {
                "identifier": "openai:llama-3.3-70b-versatile",
                "api_key_env_var": "GROQ_API_KEY",
                "params": {
                    "base_url": "https://api.groq.com/openai/v1",
                    "temperature": 0.7,
                },
            },
            "gpt-4.1": {
                "identifier": "openai:gpt-4.1",
                "params": {
                    "temperature": 1.0,
                },
            },
        }


# Global settings instance
settings = Settings()
