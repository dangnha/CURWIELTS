from app.agents.base_agent import BaseAgent, AgentContext, AgentResult
from app.utils.text_processing import json_loads


class LexicalResourceAgent(BaseAgent):
    agent_name = "lexical_resource"

    def get_system_prompt(self, context: AgentContext) -> str:
        return f"""You are an IELTS examiner evaluating Lexical Resource.
Evaluate: vocabulary range, precision, collocation, style/register awareness, spelling/word formation, use of uncommon/idiomatic items, repetition detection.

Knowledge base context:
{context.kb_context}

Respond in JSON:
{{
  "band_score": 0-9,
  "sub_criteria_scores": {{
    "vocabulary_range": 0-9,
    "lexical_accuracy": 0-9,
    "spelling_word_formation": 0-9
  }},
  "collocation_accuracy": "excellent|good|some_issues|poor",
  "style_appropriateness": "excellent|good|some_issues|poor",
  "repetition_issues": ["..."],
  "strengths": ["..."],
  "weaknesses": ["..."],
  "reasoning": "...",
  "confidence": 0.0-1.0
}}"""

    def get_user_prompt(self, context: AgentContext) -> str:
        return f"Essay:\n{context.essay_text}"

    def parse_response(self, raw: str) -> AgentResult:
        data = json_loads(raw)
        return AgentResult(
            agent_name=self.agent_name,
            band_score=float(data.get("band_score", 5)),
            reasoning=data.get("reasoning", ""),
            raw_response=raw,
            confidence=float(data.get("confidence", 0.8)),
            metadata={
                "sub_criteria_scores": data.get("sub_criteria_scores", {}),
                "collocation_accuracy": data.get("collocation_accuracy", ""),
                "style_appropriateness": data.get("style_appropriateness", ""),
                "repetition_issues": data.get("repetition_issues", []),
                "strengths": data.get("strengths", []),
                "weaknesses": data.get("weaknesses", []),
            },
        )
