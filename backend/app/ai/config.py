from typing import Optional
import anthropic
import openai
from app.core.config import settings

# Initialize AI clients
anthropic_client: Optional[anthropic.Anthropic] = None
openai_client: Optional[openai.OpenAI] = None


def init_ai_clients():
    """Initialize AI clients if API keys are available"""
    global anthropic_client, openai_client

    if settings.ANTHROPIC_API_KEY:
        anthropic_client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY
        )

    if settings.OPENAI_API_KEY:
        openai_client = openai.OpenAI(
            api_key=settings.OPENAI_API_KEY
        )


def is_ai_available() -> dict:
    """Check which AI services are available"""
    return {
        "claude": anthropic_client is not None,
        "openai": openai_client is not None,
        "any": anthropic_client is not None or openai_client is not None
    }


# Initialize clients on import
init_ai_clients()
