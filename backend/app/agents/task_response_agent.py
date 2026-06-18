from app.agents.base_agent import BaseAgent, AgentContext, AgentResult
from app.utils.text_processing import json_loads


class TaskResponseAgent(BaseAgent):
    agent_name = "task_response"

    def get_system_prompt(self, context: AgentContext) -> str:
        essay_type_info = f"Detected essay type: {context.essay_type}" if context.essay_type else ""
        return f"""You are an IELTS examiner evaluating Task Achievement (Task 1) or Task Response (Task 2).
Evaluate how well the essay addresses all parts of the task, presents a clear position, develops main ideas, and provides relevant supporting evidence.

{essay_type_info}

Knowledge base context:
{context.kb_context}

Respond in JSON:
{{
  "band_score": 0-9,
  "sub_criteria_scores": {{
    "relevance_to_prompt": 0-9,
    "key_data_selection": 0-9,
    "depth_of_ideas": 0-9,
    "appropriateness_of_format": 0-9,
    "data_accuracy": 0-9,
    "appropriate_word_count": 0-9
  }},
  "strengths": ["..."],
  "weaknesses": ["..."],
  "missing_requirements": ["..."],
  "position_clarity": "clear|somewhat_clear|unclear",
  "idea_development": "well_developed|adequate|limited|poor",
  "reasoning": "...",
  "confidence": 0.0-1.0
}}"""

    def get_user_prompt(self, context: AgentContext) -> str:
        prompt_info = f"\nPrompt: {context.prompt_text}" if context.prompt_text else ""
        return f"Essay:{prompt_info}\n\n{context.essay_text}"

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
                "strengths": data.get("strengths", []),
                "weaknesses": data.get("weaknesses", []),
                "missing_requirements": data.get("missing_requirements", []),
                "position_clarity": data.get("position_clarity", ""),
                "idea_development": data.get("idea_development", ""),
            },
        )
