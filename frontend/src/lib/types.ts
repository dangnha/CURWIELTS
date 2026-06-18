export interface User {
  id: string
  username: string
  email?: string
  target_band?: number
  native_language: string
  created_at: string
}

export interface Essay {
  id: string
  task_type: string
  essay_type?: string
  prompt_text?: string
  essay_text: string
  exam_label?: string
  image_path?: string
  word_count: number
  status: string
  created_at: string
}

export interface EssayList {
  items: Essay[]
  total: number
  page: number
  page_size: number
}

export interface CriteriaScoreItem {
  criterion: string
  score: number
  sub_criteria_scores?: Record<string, number>
  strengths?: string
  weaknesses?: string
  detailed_feedback?: string
}

export interface AgentStatus {
  agent_name: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  band_score?: number
  error_message?: string
}

export interface ScoringProgress {
  total_agents: number
  completed_agents: number
  agent_statuses: Record<string, AgentStatus>
}

export interface ScoringResult {
  essay_id: string
  session_id: string
  status: string
  overall_band?: number
  criteria: CriteriaScoreItem[]
  sub_criteria_scores?: Record<string, Record<string, number>>
  progress?: ScoringProgress
}

export interface VocabularyItem {
  id: string
  word: string
  lemma?: string
  pos?: string
  cefr_level?: string
  is_academic: boolean
  context_sentence?: string
  usage_accuracy?: number
  suggestion?: string
}

export interface VocabularyStats {
  total_unique: number
  by_cefr: Record<string, number>
  academic_count: number
  error_count: number
}

export interface VocabularyList {
  items: VocabularyItem[]
  stats?: VocabularyStats
  total: number
  page: number
  page_size: number
}

export interface ErrorRecord {
  id: string
  error_type: string
  severity: string
  error_text: string
  correction?: string
  explanation?: string
  position_start?: number
  position_end?: number
}

export interface Feedback {
  overall_assessment?: string
  paragraph_analysis?: ParagraphAnalysis[]
  structure_improvement?: StructureImprovement
  vocabulary_table?: VocabTableItem[]
  sentence_diversity?: SentenceDiversityItem[]
  coherence_improvement?: CoherenceImprovementItem[]
  band_upgrade_suggestions?: BandUpgradeSuggestion[]
  sample_essays?: SampleEssays
  criterion_feedback?: Record<string, string>
  priority_weakness?: string
  recommended_exercises?: string[]
  reasoning?: string
}

export interface ParagraphAnalysis {
  paragraph_label: string
  original_text: string
  comments: {
    task_response: string
    coherence_cohesion: string
    grammatical_range: string
    lexical_resource: string
  }
  how_to_rewrite: string
}

export interface StructureImprovement {
  task_type: string
  key_tips: string[]
  recommended_outline: {
    section: string
    example_topic_sentence: string
  }[]
}

export interface VocabTableItem {
  word: string
  word_type: string
  definition_vn: string
}

export interface SentenceDiversityItem {
  grammar_structure: string
  original_sentence: string
  rephrased_sentence: string
}

export interface CoherenceImprovementItem {
  original_text: string
  improved_text: string
  explanation: string
}

export interface SampleEssays {
  corrected_essay: string
  model_essay_band_8_9: string
}

export interface BandUpgradeSuggestion {
  target_band: number
  required_improvements: string[]
  example_revisions: string[]
}

export interface ProgressPoint {
  date: string
  overall_band?: number
  task_response?: number
  coherence_cohesion?: number
  lexical_resource?: number
  grammatical_range?: number
}

export interface ProgressData {
  points: ProgressPoint[]
  trend: string
  strongest_criterion?: string
  weakest_criterion?: string
  estimated_next_band?: number
}
