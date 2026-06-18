from app.agents.base_agent import BaseAgent, AgentContext, AgentResult
from app.utils.text_processing import json_loads


class ErrorAnalysisAgent(BaseAgent):
    agent_name = "error_analysis"

    def get_system_prompt(self, context: AgentContext) -> str:
        return f"""You are an IELTS writing error analyst. Identify specific errors in the essay.
Categorize each error: grammar (tense, article, preposition, subject_verb_agreement, sentence_structure), spelling, punctuation, word_choice, collocation, coherence (weak_transition, missing_topic_sentence).
For each error provide: error type, severity (minor/moderate/severe), the incorrect text, corrected text, and explanation.

Knowledge base context:
{context.kb_context}

Respond in JSON:
{{
  "errors": [
    {{
      "error_type": "grammar|spelling|punctuation|word_choice|collocation|coherence",
      "subtype": "tense|article|preposition|...",
      "severity": "minor|moderate|severe",
      "error_text": "...",
      "correction": "...",
      "explanation": "..."
    }}
  ],
  "error_summary": {{
    "total_errors": number,
    "by_type": {{}},
    "by_severity": {{}}
  }},
  "reasoning": "..."
}}"""

    def get_user_prompt(self, context: AgentContext) -> str:
        return f"Essay:\n{context.essay_text}"

    def parse_response(self, raw: str) -> AgentResult:
        data = json_loads(raw)
        errors = data.get("errors", [])
        return AgentResult(
            agent_name=self.agent_name,
            band_score=None,
            reasoning=data.get("reasoning", ""),
            raw_response=raw,
            confidence=0.85,
            metadata={
                "errors": errors,
                "error_summary": data.get("error_summary", {"total_errors": len(errors), "by_type": {}, "by_severity": {}}),
            },
        )
