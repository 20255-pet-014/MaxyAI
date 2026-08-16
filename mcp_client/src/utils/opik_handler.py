"""Opik configuration and tracking utilities."""

import opik
from google import genai
from opik.integrations.genai import track_genai

from ..settings import settings


def configure_opik() -> bool:
    """Configure Opik monitoring if all required settings are provided.

    Returns:
        bool: True if Opik was configured, False otherwise
    """
    if settings.opik_api_key and settings.opik_api_key.get_secret_value().strip():
        try:
            opik.configure(
                api_key=settings.opik_api_key.get_secret_value(),
                workspace=settings.opik_workspace,
                use_local=False,
                force=True,
                automatic_approvals=True,
            )
            return True
        except Exception:
            return False
    return False


def track_genai_client(client: genai.Client) -> genai.Client:
    """Track a Gemini client with Opik if configured.

    Args:
        client: The Gemini client to track

    Returns:
        The tracked client if Opik is configured, otherwise the original client
    """
    if settings.opik_api_key and settings.opik_api_key.get_secret_value().strip():
        return track_genai(client, project_name=settings.opik_project_name)
    return client
