from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime


# ── Auth ──
class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    email: Optional[str] = None
    password: str = Field(min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: Optional[str]
    target_band: Optional[float]
    native_language: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    target_band: Optional[float] = None
    native_language: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Essay ──
class EssayCreate(BaseModel):
    task_type: Literal["task1", "task2"]
    essay_text: str = Field(min_length=1)
    prompt_text: Optional[str] = None


class EssayResponse(BaseModel):
    id: str
    task_type: str
    essay_type: Optional[str]
    prompt_text: Optional[str]
    essay_text: str
    word_count: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class EssayListResponse(BaseModel):
    items: list[EssayResponse]
    total: int
    page: int
    page_size: int


# ── Scoring ──
class CriteriaScoreItem(BaseModel):
    criterion: str
    score: float
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    detailed_feedback: Optional[str] = None


class AgentProgress(BaseModel):
    agent_name: str
    status: Literal["pending", "running", "completed", "failed"]
    band_score: Optional[float] = None
    error_message: Optional[str] = None


class ScoringProgress(BaseModel):
    total_agents: int
    completed_agents: int
    agent_statuses: dict[str, AgentProgress]


class ScoringResultResponse(BaseModel):
    essay_id: str
    session_id: str
    status: str
    overall_band: Optional[float] = None
    criteria: list[CriteriaScoreItem] = []
    progress: Optional[ScoringProgress] = None


class BandUpgradeStep(BaseModel):
    target_band: float
    required_improvements: list[str]
    example_revisions: list[str] = []


class BandUpgradeResponse(BaseModel):
    current_band: float
    steps: list[BandUpgradeStep]


# ── Vocabulary ──
class VocabularyItemResponse(BaseModel):
    id: str
    word: str
    lemma: Optional[str]
    pos: Optional[str]
    cefr_level: Optional[str]
    is_academic: bool
    context_sentence: Optional[str]
    usage_accuracy: Optional[float]
    suggestion: Optional[str]

    class Config:
        from_attributes = True


class VocabularyStats(BaseModel):
    total_unique: int
    by_cefr: dict[str, int]
    academic_count: int
    error_count: int


class VocabularyListResponse(BaseModel):
    items: list[VocabularyItemResponse]
    stats: Optional[VocabularyStats] = None
    total: int
    page: int
    page_size: int


# ── Error ──
class ErrorRecordResponse(BaseModel):
    id: str
    error_type: str
    severity: str
    error_text: str
    correction: Optional[str]
    explanation: Optional[str]
    position_start: Optional[int]
    position_end: Optional[int]

    class Config:
        from_attributes = True


# ── Feedback / Learning Plan ──
class FocusArea(BaseModel):
    criterion: str
    priority: int
    action_items: list[str]


class LearningPlanResponse(BaseModel):
    id: str
    focus_areas: list[FocusArea]
    recommended_exercises: list[str]
    target_next_band: Optional[float]
    generated_at: datetime
    valid_until: Optional[datetime]

    class Config:
        from_attributes = True


class ProgressPoint(BaseModel):
    date: str
    overall_band: Optional[float]
    task_response: Optional[float]
    coherence_cohesion: Optional[float]
    lexical_resource: Optional[float]
    grammatical_range: Optional[float]


class ProgressResponse(BaseModel):
    points: list[ProgressPoint]
    trend: str
    strongest_criterion: Optional[str]
    weakest_criterion: Optional[str]
    estimated_next_band: Optional[float]


# ── Admin / Settings ──
class LLMProviderSettings(BaseModel):
    provider: Literal["gemini", "chatgpt", "deepseek", "grok"]
    api_key: str
    model: Optional[str] = None
    temperature: float = 0.3
    max_tokens: int = 4096


class AdminSettings(BaseModel):
    default_llm_provider: str
    default_llm_model: str
    temperature: float
    max_concurrent_llm_calls: int
    provider_configs: list[LLMProviderSettings] = []


class LLMUsageStats(BaseModel):
    total_requests: int
    total_tokens: int
    total_cost_usd: float
    by_provider: dict[str, dict]
