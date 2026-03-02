"""Thin wrapper around LLM providers for content generation."""

from __future__ import annotations

from socialmonitor.config import settings


async def generate_text(prompt: str, system: str = "", max_tokens: int = 1024) -> str:
    """Generate text using the best available LLM provider.

    Preference order: Anthropic -> OpenAI.
    Returns the generated text or raises if no provider is configured.
    """
    if settings.has_anthropic:
        return await _generate_anthropic(prompt, system, max_tokens)
    if settings.has_openai:
        return await _generate_openai(prompt, system, max_tokens)
    raise RuntimeError(
        "No LLM provider configured. Set ANTHROPIC_API_KEY or OPENAI_API_KEY."
    )


def get_model_name() -> str:
    """Return the model identifier that will be used."""
    if settings.has_anthropic:
        return "claude-sonnet-4-6"
    if settings.has_openai:
        return "gpt-4o"
    return "none"


# ---- Provider implementations ------------------------------------------------


async def _generate_anthropic(prompt: str, system: str, max_tokens: int) -> str:
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    kwargs: dict = {
        "model": "claude-sonnet-4-6",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system
    message = await client.messages.create(**kwargs)
    return message.content[0].text


async def _generate_openai(prompt: str, system: str, max_tokens: int) -> str:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    resp = await client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content or ""
