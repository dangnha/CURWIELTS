import asyncio
import logging
import re
from app.config import settings
from app.llm.base import BaseLLMProvider, LLMResponse, LLMConfig
from app.llm.gemini import GeminiProvider
from app.llm.chatgpt import ChatGPTProvider
from app.llm.deepseek import DeepSeekProvider
from app.llm.grok import GrokProvider
from app.llm.groq import GroqProvider

logger = logging.getLogger(__name__)

# Caps how many LLM requests this process has in flight at once, across all
# agents/providers. Free-tier rate limits (especially Groq's per-minute
# limits) get tripped by the pipeline's parallel agent calls otherwise —
# this turns "fire 3 calls at once" into "fire 3, run at most N concurrently".
_llm_semaphore = asyncio.Semaphore(settings.max_concurrent_llm_calls)

RATE_LIMIT_MAX_RETRIES = 3

PROVIDER_CLASSES: dict[str, type[BaseLLMProvider]] = {
    "gemini": GeminiProvider,
    "chatgpt": ChatGPTProvider,
    "deepseek": DeepSeekProvider,
    "grok": GrokProvider,
    "groq": GroqProvider,
}

DEFAULT_MODELS = {
    "gemini": "gemini-2.0-flash",
    "chatgpt": "gpt-4o-mini",
    "deepseek": "deepseek-chat",
    "grok": "grok-4.3",
    "groq": "llama-3.3-70b-versatile",
}


def get_provider(config: LLMConfig) -> BaseLLMProvider:
    cls = PROVIDER_CLASSES.get(config.provider)
    if cls is None:
        raise ValueError(f"Unknown provider: {config.provider}")
    if not config.model:
        config.model = DEFAULT_MODELS.get(config.provider, "")
    return cls(config)


def _is_rate_limit_error(e: Exception) -> bool:
    msg = str(e).lower()
    return any(kw in msg for kw in ("429", "413", "rate limit", "rate_limit", "resource_exhausted", "quota", "tokens per minute", "tpm", "too large for model"))


def _extract_retry_after_seconds(e: Exception) -> float | None:
    """Pull a provider-suggested wait time out of the error, if it gave one.

    Groq/OpenAI-style messages say things like "Please try again in 12.34s".
    Falling back to our own backoff schedule otherwise.
    """
    match = re.search(r"try again in (\d+(?:\.\d+)?)\s*s", str(e), re.IGNORECASE)
    return float(match.group(1)) if match else None


async def llm_complete(config: LLMConfig, system: str, user: str, response_format: str = "json", image_path: str | None = None) -> LLMResponse:
    provider = get_provider(config)
    last_error: Exception | None = None

    async with _llm_semaphore:
        for attempt in range(RATE_LIMIT_MAX_RETRIES):
            try:
                return await provider.complete(system=system, user=user, response_format=response_format, image_path=image_path)
            except Exception as e:
                last_error = e
                if not _is_rate_limit_error(e) or attempt == RATE_LIMIT_MAX_RETRIES - 1:
                    raise
                wait = _extract_retry_after_seconds(e) or (attempt + 1) * 8
                logger.warning("[%s] Rate limited, retrying in %.1fs (attempt %d/%d)", config.provider, wait, attempt + 1, RATE_LIMIT_MAX_RETRIES)
                await asyncio.sleep(wait)

    raise last_error or RuntimeError("LLM call failed")


def classify_llm_error(e: Exception) -> str:
    """Turn a raw provider exception into a short, human-readable reason."""
    msg = str(e).lower()
    if "quota" in msg or "429" in msg or "resource_exhausted" in msg:
        return "Quota exceeded — try a different API key or wait for quota reset."
    if "401" in msg or "403" in msg or "invalid" in msg and "key" in msg or ("api" in msg and "key" in msg):
        return "Invalid API key — check the key in Settings."
    if "timeout" in msg or "timed out" in msg:
        return "Request timed out — the provider may be slow or unreachable."
    if "connection" in msg or "network" in msg or "dns" in msg:
        return "Network error — could not reach the provider."
    return str(e)[:200]
