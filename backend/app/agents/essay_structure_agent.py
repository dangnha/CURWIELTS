import json
from app.agents.base_agent import BaseAgent, AgentContext, AgentResult
from app.utils.text_processing import json_loads


class EssayStructureAgent(BaseAgent):
    agent_name = "essay_structure"

    def get_system_prompt(self, context: AgentContext) -> str:
        return f"""You are an IELTS essay structure analyst. Analyze the given essay and determine:
1. Whether it's Task 1 or Task 2
2. The specific essay type (for Task 1: bar_chart, line_graph, pie_chart, table, process, map, mixed; for Task 2: opinion, discussion, advantages_disadvantages, positive_negative, two_part_question, problem_solution, direct_question)
3. Whether the essay has proper structure (introduction, body paragraphs, conclusion/overview)
4. Structural strengths and weaknesses
5. A structural band score (1-9)

Knowledge base context:
{context.kb_context}

Respond in JSON format:
{{
  "task_type": "task1|task2",
  "essay_type": "...",
  "has_introduction": true/false,
  "has_body_paragraphs": true/false,
  "has_conclusion_or_overview": true/false,
  "paragraph_count": number,
  "structural_band_score": 0-9,
  "strengths": ["..."],
  "weaknesses": ["..."],
  "reasoning": "..."
}}"""

    def get_user_prompt(self, context: AgentContext) -> str:
        return f"Essay:\n{context.essay_text}"

    def parse_response(self, raw: str) -> AgentResult:
        data = json_loads(raw)
        return AgentResult(
            agent_name=self.agent_name,
            band_score=float(data.get("structural_band_score", 5)),
            reasoning=data.get("reasoning", ""),
            raw_response=raw,
            confidence=0.85,
            metadata={
                "essay_type": data.get("essay_type"),
                "task_type": data.get("task_type"),
                "has_introduction": data.get("has_introduction", False),
                "has_body_paragraphs": data.get("has_body_paragraphs", False),
                "has_conclusion_or_overview": data.get("has_conclusion_or_overview", False),
                "paragraph_count": data.get("paragraph_count", 1),
                "strengths": data.get("strengths", []),
                "weaknesses": data.get("weaknesses", []),
            },
        )
