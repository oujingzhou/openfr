"""
Utilities for structured output with fallback to free-text generation.
"""

import logging
from typing import Any, Callable, TypeVar

from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel

from openfr.agents.utils.content import extract_text

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def bind_structured(
    llm: BaseChatModel, schema: type[T], agent_name: str
) -> BaseChatModel:
    """
    Bind a Pydantic schema to an LLM for structured output.

    Args:
        llm: The base LLM
        schema: Pydantic model class
        agent_name: Agent name for logging

    Returns:
        LLM with structured output binding (or original LLM if not supported)
    """
    try:
        return llm.with_structured_output(schema)
    except (AttributeError, NotImplementedError):
        logger.warning(
            f"{agent_name}: Provider does not support structured output, "
            "will fall back to free-text generation"
        )
        return llm


def invoke_structured_or_freetext(
    structured_llm: BaseChatModel,
    fallback_llm: BaseChatModel,
    prompt: Any,
    render_fn: Callable[[T], str],
    agent_name: str,
) -> str:
    """
    Invoke LLM with structured output, falling back to free-text if needed.

    Args:
        structured_llm: LLM bound with structured output
        fallback_llm: Original LLM for fallback
        prompt: Prompt (string or messages list)
        render_fn: Function to render structured output to string
        agent_name: Agent name for logging

    Returns:
        Rendered string output
    """
    try:
        # Try structured output first
        result = structured_llm.invoke(prompt)
        if isinstance(result, BaseModel):
            return render_fn(result)
        # If result is not a Pydantic model, it's already free-text
        return extract_text(result.content) if hasattr(result, "content") else str(result)
    except Exception as e:
        logger.warning(
            f"{agent_name}: Structured output failed ({e}), falling back to free-text"
        )
        # Fallback to free-text generation
        response = fallback_llm.invoke(prompt)
        return extract_text(response.content) if hasattr(response, "content") else str(response)
