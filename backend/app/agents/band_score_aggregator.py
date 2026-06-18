from app.agents.base_agent import BaseAgent, AgentContext, AgentResult
from app.utils.text_processing import json_loads


class BandScoreAggregatorAgent(BaseAgent):
    agent_name = "band_score_aggregator"

    def get_system_prompt(self, context: AgentContext) -> str:
        tr = context.previous_results.get("task_response", {})
        cc = context.previous_results.get("coherence_cohesion", {})
        lr = context.previous_results.get("lexical_resource", {})
        gra = context.previous_results.get("grammatical_range", {})

        return f"""You are an IELTS band score aggregator. Given the 4 criterion scores, calculate the overall band score using the standard IELTS rounding rules (average the 4 criteria, round to nearest 0.5, with .25 rounding up and .75 rounding up to next whole band).
Also provide weighted rationale, confidence level, and a summary.

Criterion scores:
- Task Response: {tr.get('band_score', 'N/A')}
- Coherence & Cohesion: {cc.get('band_score', 'N/A')} 
- Lexical Resource: {lr.get('band_score', 'N/A')}
- Grammatical Range & Accuracy: {gra.get('band_score', 'N/A')}

Knowledge base context:
{context.kb_context}

Respond in JSON:
{{
  "overall_band": 0-9,
  "criteria_breakdown": {{
    "task_response": number,
    "coherence_cohesion": number,
    "lexical_resource": number,
    "grammatical_range_accuracy": number
  }},
  "average": number,
  "rounding_explanation": "...",
  "overall_assessment": "...",
  "reasoning": "...",
  "confidence": 0.0-1.0
}}"""

    def get_user_prompt(self, context: AgentContext) -> str:
        return "Calculate the overall band score."

    def parse_response(self, raw: str) -> AgentResult:
        data = json_loads(raw)
        return AgentResult(
            agent_name=self.agent_name,
            band_score=float(data.get("overall_band", 5)),
            reasoning=data.get("reasoning", ""),
            raw_response=raw,
            confidence=float(data.get("confidence", 0.9)),
            metadata={
                "criteria_breakdown": data.get("criteria_breakdown", {}),
                "average": data.get("average", 0),
                "rounding_explanation": data.get("rounding_explanation", ""),
                "overall_assessment": data.get("overall_assessment", ""),
            },
        )
