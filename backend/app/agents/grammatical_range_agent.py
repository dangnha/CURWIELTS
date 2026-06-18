from app.agents.base_agent import BaseAgent, AgentContext, AgentResult
from app.utils.text_processing import json_loads


class GrammaticalRangeAgent(BaseAgent):
    agent_name = "grammatical_range"

    def get_system_prompt(self, context: AgentContext) -> str:
        return f"""You are an IELTS examiner evaluating Grammatical Range & Accuracy.
Evaluate: sentence variety (simple, compound, complex), grammatical accuracy, tense usage, article usage, preposition usage, subject-verb agreement, punctuation, and specific grammar errors.

Knowledge base context:
{context.kb_context}

Respond in JSON:
{{
  "band_score": 0-9,
  "sub_criteria_scores": {{
    "sentence_structure_variety": 0-9,
    "grammar_accuracy": 0-9,
    "punctuation_usage": 0-9
  }},
  "grammar_variety": "wide|adequate|limited|very_limited",
  "sentence_complexity": "high|moderate|low",
  "grammar_errors": [
    {{
      "error_type": "tense|article|preposition|subject_verb_agreement|sentence_structure|punctuation|other",
      "incorrect_text": "...",
      "correction": "...",
      "explanation": "..."
    }}
  ],
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
                "grammar_variety": data.get("grammar_variety", ""),
                "sentence_complexity": data.get("sentence_complexity", ""),
                "grammar_errors": data.get("grammar_errors", []),
                "strengths": data.get("strengths", []),
                "weaknesses": data.get("weaknesses", []),
            },
        )
