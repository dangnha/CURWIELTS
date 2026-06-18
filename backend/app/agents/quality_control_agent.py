from app.agents.base_agent import BaseAgent, AgentContext, AgentResult
from app.utils.text_processing import json_loads


class QualityControlAgent(BaseAgent):
    agent_name = "quality_control"

    def get_system_prompt(self, context: AgentContext) -> str:
        tr = context.previous_results.get("task_response", {})
        cc = context.previous_results.get("coherence_cohesion", {})
        lr = context.previous_results.get("lexical_resource", {})
        gra = context.previous_results.get("grammatical_range", {})
        agg = context.previous_results.get("band_score_aggregator", {})

        return f"""You are a quality control agent for IELTS essay scoring. Cross-validate the scoring outputs.
Check for:
- Score consistency (if any criterion differs from others by >2 bands, flag it)
- Hallucination or fabricated errors
- Assessment contradiction between agents

Scores received:
- Task Response: {tr.get('band_score')}
- Coherence & Cohesion: {cc.get('band_score')}
- Lexical Resource: {lr.get('band_score')}
- Grammatical Range: {gra.get('band_score')}
- Aggregated overall: {agg.get('band_score')}

Respond in JSON:
{{
  "is_valid": true/false,
  "anomalies": ["..."],
  "needs_rescoring": ["..."],
  "confidence_adjustment": 0.0 (reduce by this if anomalies found),
  "final_overall_band": number,
  "reasoning": "..."
}}"""

    def get_user_prompt(self, context: AgentContext) -> str:
        return "Cross-validate the scoring results."

    def parse_response(self, raw: str) -> AgentResult:
        data = json_loads(raw)
        return AgentResult(
            agent_name=self.agent_name,
            band_score=float(data.get("final_overall_band", 0)),
            reasoning=data.get("reasoning", ""),
            raw_response=raw,
            confidence=1.0 - float(data.get("confidence_adjustment", 0)),
            metadata={
                "is_valid": data.get("is_valid", True),
                "anomalies": data.get("anomalies", []),
                "needs_rescoring": data.get("needs_rescoring", []),
                "confidence_adjustment": data.get("confidence_adjustment", 0),
            },
        )
