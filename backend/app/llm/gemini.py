import time
import mimetypes
import json as json_mod
from pathlib import Path
from app.llm.base import BaseLLMProvider, LLMResponse, LLMConfig


class GeminiProvider(BaseLLMProvider):
    def get_model_name(self) -> str:
        return self.config.model

    async def complete(self, system: str, user: str, response_format: str = "text", image_path: str | None = None) -> LLMResponse:
        import google.generativeai as genai
        genai.configure(api_key=self.config.api_key)

        prompt = f"{system}\n\n{user}"
        content: list = [prompt]
        if image_path and Path(image_path).exists():
            mime_type = mimetypes.guess_type(image_path)[0] or "image/png"
            content.append({"mime_type": mime_type, "data": Path(image_path).read_bytes()})

        generation_config = {
            "temperature": self.config.temperature,
            "max_output_tokens": self.config.max_tokens,
        }
        if response_format == "json":
            generation_config["response_mime_type"] = "application/json"

        # Rate-limit retry/backoff is handled centrally by app.llm.router.llm_complete
        # (uniformly across all providers, with non-blocking asyncio.sleep).
        t0 = time.time()
        model = genai.GenerativeModel(self.config.model, generation_config=generation_config)
        response = await model.generate_content_async(content)
        latency = int((time.time() - t0) * 1000)

        result_text = response.text or ""
        usage = response.usage_metadata
        prompt_tokens = usage.prompt_token_count if usage else 0
        completion_tokens = usage.candidates_token_count if usage else 0

        return LLMResponse(
            content=result_text,
            model=self.config.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            latency_ms=latency,
            cost_usd=0.0,
        )
