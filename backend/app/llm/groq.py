import time
from app.llm.base import BaseLLMProvider, LLMResponse, LLMConfig


class GroqProvider(BaseLLMProvider):
    def get_model_name(self) -> str:
        return self.config.model

    async def complete(self, system: str, user: str, response_format: str = "text", image_path: str | None = None) -> LLMResponse:
        # GroqCloud serves an OpenAI-compatible Chat Completions API. Most
        # hosted text models support response_format json_object; vision is
        # not available on the default text models, so image_path is
        # accepted for interface parity but intentionally not sent.
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.config.api_key, base_url="https://api.groq.com/openai/v1")
        t0 = time.time()
        kwargs = {
            "model": self.config.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        if response_format == "json":
            kwargs["response_format"] = {"type": "json_object"}

        response = await client.chat.completions.create(**kwargs)
        latency = int((time.time() - t0) * 1000)
        usage = response.usage
        return LLMResponse(
            content=response.choices[0].message.content or "",
            model=self.config.model,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
            latency_ms=latency,
            cost_usd=0.0,
        )
