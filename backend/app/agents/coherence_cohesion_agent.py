from app.agents.base_agent import BaseAgent, AgentContext, AgentResult
from app.utils.text_processing import json_loads


class CoherenceCohesionAgent(BaseAgent):
    agent_name = "coherence_cohesion"

    def get_system_prompt(self, context: AgentContext) -> str:
        return f"""You are an IELTS examiner evaluating Coherence & Cohesion.
Evaluate: paragraph organization, logical flow, cohesive devices (linking words, referencing, substitution), overall progression, and paragraph topic clarity.

Knowledge base context:
{context.kb_context}

Respond in JSON:
{{
  "band_score": 0-9,
  "sub_criteria_scores": {{
    "logical_organization": 0-9,
    "effective_intro_conclusion": 0-9,
    "supported_main_points": 0-9,
    "cohesive_devices_usage": 0-9,
    "paragraphing": 0-9
  }},
  "paragraph_organization": "excellent|good|adequate|poor",
  "logical_flow": "excellent|good|adequate|poor",
  "cohesive_devices_used": ["..."],
  "cohesive_device_issues": ["..."],
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
                "paragraph_organization": data.get("paragraph_organization", ""),
                "logical_flow": data.get("logical_flow", ""),
                "cohesive_devices_used": data.get("cohesive_devices_used", []),
                "cohesive_device_issues": data.get("cohesive_device_issues", []),
                "strengths": data.get("strengths", []),
                "weaknesses": data.get("weaknesses", []),
            },
        )
