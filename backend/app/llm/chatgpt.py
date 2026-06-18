import time
import base64
import mimetypes
from pathlib import Path
from app.llm.base import BaseLLMProvider, LLMResponse, LLMConfig


class ChatGPTProvider(BaseLLMProvider):
    def get_model_name(self) -> str:
        return self.config.model

    async def complete(self, system: str, user: str, response_format: str = "text", image_path: str | None = None) -> LLMResponse:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.config.api_key)

        user_content: str | list = user
        if image_path and Path(image_path).exists():
            mime_type = mimetypes.guess_type(image_path)[0] or "image/png"
            b64 = base64.b64encode(Path(image_path).read_bytes()).decode()
            user_content = [
                {"type": "text", "text": user},
                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64}"}},
            ]

        t0 = time.time()
        kwargs = {
            "model": self.config.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user_content}],
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
