from app.agents.base_agent import BaseAgent, AgentContext, AgentResult
from app.utils.text_processing import json_loads


class VocabularyExtractionAgent(BaseAgent):
    agent_name = "vocabulary_extraction"

    def get_system_prompt(self, context: AgentContext) -> str:
        return f"""You are a vocabulary analyst for IELTS essays. Extract notable vocabulary from the essay.
For each word/phrase, provide: word, part of speech, difficulty level (A1-C2), whether it's academic, the context sentence, a suggested synonym or alternative, and estimated usage accuracy (0.0-1.0).
Also identify useful grammar structures used (complex sentences, relative clauses, conditionals, passive voice, advanced patterns) and linking/cohesive devices.

Knowledge base context:
{context.kb_context}

Respond in JSON:
{{
  "vocabulary": [
    {{
      "word": "...",
      "pos": "noun|verb|adjective|adverb|phrase|...",
      "cefr_level": "A1|A2|B1|B2|C1|C2",
      "is_academic": true/false,
      "context_sentence": "...",
      "usage_accuracy": 0.0-1.0,
      "suggestion": "..."
    }}
  ],
  "grammar_structures": [
    {{"type": "complex_sentence|relative_clause|conditional|passive_voice|advanced_pattern", "example": "..."}}
  ],
  "linking_devices": ["..."],
  "reasoning": "..."
}}"""

    def get_user_prompt(self, context: AgentContext) -> str:
        return f"Essay:\n{context.essay_text}"

    def parse_response(self, raw: str) -> AgentResult:
        data = json_loads(raw)
        return AgentResult(
            agent_name=self.agent_name,
            band_score=None,
            reasoning=data.get("reasoning", ""),
            raw_response=raw,
            confidence=0.85,
            metadata={
                "vocabulary": data.get("vocabulary", []),
                "grammar_structures": data.get("grammar_structures", []),
                "linking_devices": data.get("linking_devices", []),
            },
        )
