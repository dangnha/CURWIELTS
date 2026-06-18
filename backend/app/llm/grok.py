import time
from app.llm.base import BaseLLMProvider, LLMResponse, LLMConfig


class GrokProvider(BaseLLMProvider):
    def get_model_name(self) -> str:
        return self.config.model

    async def complete(self, system: str, user: str, response_format: str = "text", image_path: str | None = None) -> LLMResponse:
        # xAI serves Grok over the Responses API (POST /v1/responses with
        # "input", not the Chat Completions "messages" shape). image_path is
        # accepted for interface parity with other providers but not sent —
        # add input_image content parts here if a vision-capable model is used.
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.config.api_key, base_url="https://api.x.ai/v1")
        t0 = time.time()
        kwargs = {
            "model": self.config.model,
            "input": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": self.config.temperature,
            "max_output_tokens": self.config.max_tokens,
        }
        if response_format == "json":
            kwargs["text"] = {"format": {"type": "json_object"}}

        response = await client.responses.create(**kwargs)
        latency = int((time.time() - t0) * 1000)
        usage = response.usage
        return LLMResponse(
            content=response.output_text or "",
            model=self.config.model,
            prompt_tokens=usage.input_tokens if usage else 0,
            completion_tokens=usage.output_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
            latency_ms=latency,
            cost_usd=0.0,
        )
