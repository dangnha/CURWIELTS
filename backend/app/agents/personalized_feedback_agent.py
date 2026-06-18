import json
from app.agents.base_agent import BaseAgent, AgentContext, AgentResult
from app.utils.text_processing import json_loads


class PersonalizedFeedbackAgent(BaseAgent):
    agent_name = "personalized_feedback"

    def get_system_prompt(self, context: AgentContext) -> str:
        tr = context.previous_results.get("task_response", {})
        cc = context.previous_results.get("coherence_cohesion", {})
        lr = context.previous_results.get("lexical_resource", {})
        gra = context.previous_results.get("grammatical_range", {})

        return f"""You are an IELTS tutor. Generate a comprehensive feedback report for the writer. Include ALL of the following sections:

Scores:
- Task Response: {tr.get('band_score')}
- Coherence & Cohesion: {cc.get('band_score')}
- Lexical Resource: {lr.get('band_score')}
- Grammatical Range: {gra.get('band_score')}

Knowledge base context:
{context.kb_context}

## SECTION 1: Overall Assessment
Provide a 2-3 sentence overview summarizing overall performance.

## SECTION 2: Paragraph-by-Paragraph Analysis
For EACH paragraph in the essay, provide:
- The original text of the paragraph (copy exactly)
- "Comments" - evaluate task response, coherence, grammar, and vocabulary for this paragraph specifically
- "How to rewrite" - provide an improved version of the paragraph with better vocabulary, grammar, and flow

## SECTION 3: Essay Structure & Argument Improvement
- "task_type" - the detected IELTS task type
- "key_tips" - list of 3-5 key writing tips for this task type
- "recommended_outline" - recommended essay structure with topic sentence examples for each section

## SECTION 4: Vocabulary Table
List 10 new/notable vocabulary words relevant to this topic:
For each: {{"word": "...", "word_type": "noun/verb/adjective/adverb/phrase", "definition_vn": "Tiếng Việt definition"}}

## SECTION 5: Sentence Structure Diversity
Show 5 examples of grammar transformations:
For each: {{"grammar_structure": "<name, e.g. Compound Sentence>", "original_sentence": "<from essay>", "rephrased_sentence": "<improved version>"}}

## SECTION 6: Coherence & Cohesion Improvement
Show 5 before/after examples of coherence improvements:
For each: {{"original_text": "...", "improved_text": "...", "explanation": "why this improves flow (in Vietnamese)"}}

## SECTION 7: Band Upgrade Path
For each higher band level, describe what needs to improve:
For each: {{"target_band": <float>, "required_improvements": ["..."], "example_revisions": ["..."]}}

## SECTION 8: Sample Essays
- "corrected_essay": the full essay with all errors fixed, written at intermediate vocabulary level (Band 5.5-6.5)
- "model_essay_band_8_9": a model essay on the same topic achieving Band 8-9 level, with sophisticated vocabulary and complex grammar

## SECTION 9: Priority & Exercises
- "priority_weakness": the single most urgent issue to fix
- "recommended_exercises": list of 3-5 specific exercises

You MUST respond with valid JSON only. Use this exact structure:
{{
  "overall_assessment": "<2-3 sentences>",
  "paragraph_analysis": [
    {{
      "paragraph_label": "Introduction/Body 1/Body 2/Conclusion",
      "original_text": "<exact paragraph from essay>",
      "comments": {{
        "task_response": "<analysis in Vietnamese>",
        "coherence_cohesion": "<analysis in Vietnamese>",
        "grammatical_range": "<analysis in Vietnamese>",
        "lexical_resource": "<analysis in Vietnamese>"
      }},
      "how_to_rewrite": "<improved paragraph in English>"
    }}
  ],
  "structure_improvement": {{
    "task_type": "<detected task type>",
    "key_tips": ["<tip 1>", "<tip 2>", "<tip 3>"],
    "recommended_outline": [
      {{
        "section": "Introduction",
        "example_topic_sentence": "<example sentence>"
      }}
    ]
  }},
  "vocabulary_table": [
    {{"word": "...", "word_type": "noun", "definition_vn": "..."}}
  ],
  "sentence_diversity": [
    {{
      "grammar_structure": "<structure name>",
      "original_sentence": "<from essay>",
      "rephrased_sentence": "<improved version>"
    }}
  ],
  "coherence_improvement": [
    {{
      "original_text": "<from essay>",
      "improved_text": "<improved>",
      "explanation": "<in Vietnamese>"
    }}
  ],
  "band_upgrade_suggestions": [
    {{
      "target_band": <float>,
      "required_improvements": ["..."],
      "example_revisions": ["..."]
    }}
  ],
  "sample_essays": {{
    "corrected_essay": "<full corrected essay text>",
    "model_essay_band_8_9": "<full model essay Band 8-9 text>"
  }},
  "criterion_feedback": {{
    "task_response": "<feedback>",
    "coherence_cohesion": "<feedback>",
    "lexical_resource": "<feedback>",
    "grammatical_range_accuracy": "<feedback>"
  }},
  "priority_weakness": "<most urgent issue>",
  "recommended_exercises": ["<exercise 1>", "<exercise 2>", "<exercise 3>"],
  "reasoning": "<summary>"
}}"""

    def get_user_prompt(self, context: AgentContext) -> str:
        prompt = f"Essay:\n{context.essay_text}"
        if context.prompt_text:
            prompt = f"Prompt:\n{context.prompt_text}\n\n{prompt}"
        return prompt

    def parse_response(self, raw: str) -> AgentResult:
        data = json_loads(raw)
        return AgentResult(
            agent_name=self.agent_name,
            band_score=None,
            reasoning=data.get("reasoning", ""),
            raw_response=raw,
            confidence=0.85,
            metadata={
                "overall_assessment": data.get("overall_assessment", ""),
                "paragraph_analysis": data.get("paragraph_analysis", []),
                "structure_improvement": data.get("structure_improvement", {}),
                "vocabulary_table": data.get("vocabulary_table", []),
                "sentence_diversity": data.get("sentence_diversity", []),
                "coherence_improvement": data.get("coherence_improvement", []),
                "band_upgrade_suggestions": data.get("band_upgrade_suggestions", []),
                "sample_essays": data.get("sample_essays", {}),
                "criterion_feedback": data.get("criterion_feedback", {}),
                "priority_weakness": data.get("priority_weakness", ""),
                "recommended_exercises": data.get("recommended_exercises", []),
            },
        )
