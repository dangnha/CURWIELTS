from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class AgentContext:
    essay_text: str
    prompt_text: str | None
    task_type: str
    essay_type: str | None = None
    previous_results: dict = field(default_factory=dict)
    kb_context: str = ""


@dataclass
class AgentResult:
    agent_name: str
    band_score: float | None
    reasoning: str
    raw_response: str
    confidence: float
    metadata: dict = field(default_factory=dict)


class BaseAgent(ABC):
    agent_name: str = "base"

    @abstractmethod
    def get_system_prompt(self, context: AgentContext) -> str:
        ...

    @abstractmethod
    def get_user_prompt(self, context: AgentContext) -> str:
        ...

    @abstractmethod
    def parse_response(self, raw: str) -> AgentResult:
        ...
