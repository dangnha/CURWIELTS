from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: int
    cost_usd: float


@dataclass
class LLMConfig:
    provider: str
    api_key: str
    model: str
    temperature: float = 0.3
    max_tokens: int = 8192


class BaseLLMProvider(ABC):
    def __init__(self, config: LLMConfig):
        self.config = config

    @abstractmethod
    async def complete(self, system: str, user: str, response_format: str = "text", image_path: str | None = None) -> LLMResponse:
        ...

    @abstractmethod
    def get_model_name(self) -> str:
        ...
