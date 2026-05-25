from __future__ import annotations
import litellm

# Suppress LiteLLM's verbose logging
litellm.suppress_debug_info = True


def build_model_string(provider: str, model: str) -> str:
    """Return the LiteLLM model string: '{provider}/{model}'.

    LiteLLM accepts this format for Anthropic, OpenAI, and Gemini.
    Examples:
      anthropic/claude-opus-4-7
      openai/gpt-4o
      gemini/gemini-1.5-pro
    """
    return f"{provider.lower()}/{model}"
