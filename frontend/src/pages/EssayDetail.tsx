import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../lib/api'
import type { Feedback, ParagraphAnalysis as PAnalysis, StructureImprovement, VocabTableItem, SentenceDiversityItem, CoherenceImprovementItem, SampleEssays } from '../lib/types'
import { ArrowLeft, RefreshCw, CheckCircle2, XCircle, Clock, Lightbulb, Pencil, ChevronDown, ChevronRight } from 'lucide-react'

const AGENT_NAMES: Record<string, string> = {
  coherence_cohesion: 'Coherence & Cohesion',
  lexical_resource: 'Lexical Resource',
  grammatical_range: 'Grammatical Range & Accuracy',
  task_response: 'Task Response & Structure',
  vocabulary_extraction: 'Vocabulary Extraction',
  error_analysis: 'Error Detection',
  personalized_feedback: 'Feedback & Band Upgrade',
}

const CRITERION_LABELS: Record<string, string> = {
  task_response: 'Task Response',
  coherence_cohesion: 'Coherence & Cohesion',
  lexical_resource: 'Lexical Resource',
  grammatical_range_accuracy: 'Grammatical Range & Accuracy',
}

const CRITERION_AGENT_MAP: Record<string, string> = {
  task_response: 'task_response',
  coherence_cohesion: 'coherence_cohesion',
  lexical_resource: 'lexical_resource',
  grammatical_range_accuracy: 'grammatical_range',
}

const SUB_CRITERIA_LABELS: Record<string, Record<string, string>> = {
  task_response: {
    relevance_to_prompt: 'Relevance to Prompt',
    key_data_selection: 'Key Data Selection',
    depth_of_ideas: 'Depth of Ideas',
    appropriateness_of_format: 'Appropriateness of Format',
    data_accuracy: 'Data Accuracy',
    appropriate_word_count: 'Appropriate Word Count',
  },
  coherence_cohesion: {
    logical_organization: 'Logical Organization',
    effective_intro_conclusion: 'Effective Introduction & Conclusion',
    supported_main_points: 'Supported Main Points',
    cohesive_devices_usage: 'Cohesive Devices Usage',
    paragraphing: 'Paragraphing',
  },
  lexical_resource: {
    vocabulary_range: 'Vocabulary Range',
    lexical_accuracy: 'Lexical Accuracy',
    spelling_word_formation: 'Spelling and Word Formation',
  },
  grammatical_range_accuracy: {
    sentence_structure_variety: 'Sentence Structure Variety',
    grammar_accuracy: 'Grammar Accuracy',
    punctuation_usage: 'Punctuation Usage',
  },
}

const BAND_COLORS: Record<number, { bg: string; text: string; bar: string; badgeBg: string; badgeBorder: string }> = {
  9: { bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-700 dark:text-green-300', bar: 'bg-green-500', badgeBg: '#e8f5e8', badgeBorder: '#388e3c' },
  8: { bg: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-700 dark:text-blue-300', bar: 'bg-blue-500', badgeBg: '#e8f5e8', badgeBorder: '#388e3c' },
  7: { bg: 'bg-purple-100 dark:bg-purple-900/30', text: 'text-purple-700 dark:text-purple-300', bar: 'bg-purple-500', badgeBg: '#f3e5f5', badgeBorder: '#7b1fa2' },
  6: { bg: 'bg-amber-100 dark:bg-amber-900/30', text: 'text-amber-700 dark:text-amber-300', bar: 'bg-amber-500', badgeBg: '#fff3e0', badgeBorder: '#e65100' },
  5: { bg: 'bg-orange-100 dark:bg-orange-900/30', text: 'text-orange-700 dark:text-orange-300', bar: 'bg-orange-500', badgeBg: '#fbe9e7', badgeBorder: '#d84315' },
}

function getBandColor(score: number) {
  const floor = Math.min(Math.max(Math.floor(score), 5), 9)
  return BAND_COLORS[floor] || BAND_COLORS[5]
}

function BandBadge({ score }: { score: number }) {
  const rounded = Math.round(score * 2) / 2
  const colors = getBandColor(rounded)
  return (
    <div className={`inline-flex items-center justify-center w-20 h-20 rounded-full ${colors.bg} ${colors.text} text-3xl font-bold border-4 border-current`}>
      {rounded.toFixed(1)}
    </div>
  )
}

function SubCriteriaBadge({ score, label }: { score: number; label: string }) {
  const colors = getBandColor(score)
  return (
    <div className="flex items-center gap-2 py-1.5">
      <span
        className="inline-flex items-center justify-center w-7 h-7 rounded text-xs font-bold"
        style={{ color: colors.badgeBorder, backgroundColor: colors.badgeBg, border: `1px solid ${colors.badgeBorder}` }}
      >
        {Math.round(score)}
      </span>
      <span className="text-xs text-slate-600 dark:text-slate-400">{label}</span>
    </div>
  )
}

function CollapsibleSection({ title, defaultOpen = false, children }: { title: string; defaultOpen?: boolean; children: React.ReactNode }) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
      <button onClick={() => setOpen(!open)} className="w-full flex items-center justify-between p-4 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors">
        <h2 className="text-lg font-semibold text-left">{title}</h2>
        {open ? <ChevronDown className="w-5 h-5 text-slate-400" /> : <ChevronRight className="w-5 h-5 text-slate-400" />}
      </button>
      {open && <div className="px-4 pb-4 border-t border-slate-100 dark:border-slate-700">{children}</div>}
    </div>
  )
}

function CriterionCard({ data, subScores }: { data: any; subScores?: Record<string, number> }) {
  const score = data.score
  const colors = getBandColor(score)
  const strengths: string[] = Array.isArray(data.strengths) ? data.strengths : []
  const weaknesses: string[] = Array.isArray(data.weaknesses) ? data.weaknesses : []

  const criterionKey = CRITERION_AGENT_MAP[data.criterion] || ''
  const subLabels = SUB_CRITERIA_LABELS[data.criterion] || {}

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-sm uppercase tracking-wide text-slate-500 dark:text-slate-400">{CRITERION_LABELS[data.criterion] || data.criterion}</h3>
        <span className={`text-2xl font-bold ${colors.text}`}>{score.toFixed(1)}</span>
      </div>
      <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2.5 mb-4">
        <div className={`h-2.5 rounded-full transition-all ${colors.bar}`} style={{ width: `${(score / 9) * 100}%` }} />
      </div>

      {subScores && Object.keys(subLabels).length > 0 && (
        <div className="mb-4">
          {Object.entries(subLabels).map(([key, label]) => (
            <SubCriteriaBadge key={key} score={subScores[key] ?? 0} label={label} />
          ))}
        </div>
      )}

      {data.detailed_feedback && <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">{data.detailed_feedback}</p>}
      {strengths.length > 0 && (
        <div className="mb-2">
          <span className="text-xs font-semibold text-green-600 uppercase">Strengths</span>
          <ul className="list-disc list-inside text-xs text-slate-600 dark:text-slate-400 mt-1 space-y-0.5">
            {strengths.map((s: string, i: number) => <li key={i}>{s}</li>)}
          </ul>
        </div>
      )}
      {weaknesses.length > 0 && (
        <div>
          <span className="text-xs font-semibold text-red-500 uppercase">Weaknesses</span>
          <ul className="list-disc list-inside text-xs text-slate-600 dark:text-slate-400 mt-1 space-y-0.5">
            {weaknesses.map((w: string, i: number) => <li key={i}>{w}</li>)}
          </ul>
        </div>
      )}
    </div>
  )
}

function ParagraphAnalysisCard({ pa }: { pa: PAnalysis }) {
  const [showRewrite, setShowRewrite] = useState(false)
  return (
    <div className="mb-4 p-4 bg-slate-50 dark:bg-slate-700/30 rounded-lg border border-slate-100 dark:border-slate-700">
      <h4 className="font-semibold text-sm text-slate-800 dark:text-slate-200 mb-2">{pa.paragraph_label}</h4>
      <p className="text-sm italic text-slate-600 dark:text-slate-400 mb-3 border-l-2 border-blue-300 pl-3">"{pa.original_text}"</p>

      <h5 className="text-xs font-semibold text-slate-500 uppercase mb-2">Comments</h5>
      <ul className="text-xs text-slate-600 dark:text-slate-400 space-y-1 mb-3">
        {pa.comments.task_response && (
          <li><strong>Task Response:</strong> {pa.comments.task_response}</li>
        )}
        {pa.comments.coherence_cohesion && (
          <li><strong>Coherence & Cohesion:</strong> {pa.comments.coherence_cohesion}</li>
        )}
        {pa.comments.grammatical_range && (
          <li><strong>Grammar:</strong> {pa.comments.grammatical_range}</li>
        )}
        {pa.comments.lexical_resource && (
          <li><strong>Vocabulary:</strong> {pa.comments.lexical_resource}</li>
        )}
      </ul>

      <button
        onClick={() => setShowRewrite(!showRewrite)}
        className="text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center gap-1"
      >
        {showRewrite ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
        How to rewrite
      </button>
      {showRewrite && (
        <p className="text-sm text-slate-700 dark:text-slate-300 mt-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded border border-blue-100 dark:border-blue-800 italic">
          "{pa.how_to_rewrite}"
        </p>
      )}
    </div>
  )
}

export default function EssayDetail() {
  const { essayId } = useParams<{ essayId: string }>()
  const navigate = useNavigate()
  const [result, setResult] = useState<any>(null)
  const [errors, setErrors] = useState<any[]>([])
  const [feedback, setFeedback] = useState<Feedback | null>(null)
  const [bandUpgrade, setBandUpgrade] = useState<any>(null)
  const [vocab, setVocab] = useState<any[]>([])
  const [polling, setPolling] = useState(true)
  const [checkedOnce, setCheckedOnce] = useState(false)
  const [showLearn, setShowLearn] = useState(false)
  const [learning, setLearning] = useState<any>(null)
  const [learningIsCached, setLearningIsCached] = useState(false)
  const [learningLoading, setLearningLoading] = useState(false)
  const [feedbackTab, setFeedbackTab] = useState<'analysis' | 'samples'>('analysis')

  useEffect(() => {
    if (!essayId) return
    let cancelled = false
    let interval: ReturnType<typeof setInterval> | null = null

    const fetchStatus = async () => {
      try {
        const res = await api.get(`/essays/${essayId}/score`)
        if (cancelled) return
        setResult(res.data)
        setCheckedOnce(true)
        if (res.data.status === 'completed' || res.data.status === 'failed') {
          setPolling(false)
          if (interval) clearInterval(interval)
        }
      } catch {
        if (!cancelled) { setPolling(false); setCheckedOnce(true); if (interval) clearInterval(interval) }
      }
    }

    fetchStatus()
    interval = setInterval(fetchStatus, 2000)
    return () => { cancelled = true; if (interval) clearInterval(interval) }
  }, [essayId])

  useEffect(() => {
    if (result?.status === 'completed' && essayId) {
      api.get(`/essays/${essayId}/errors`).then(r => setErrors(r.data || []))
      api.get(`/essays/${essayId}/feedback`).then(r => setFeedback(r.data))
      api.get(`/essays/${essayId}/band-upgrade`).then(r => setBandUpgrade(r.data)).catch(() => {})
      api.get(`/vocabulary?page_size=100`).then(r => setVocab(r.data.items || []))
      api.get('/learning/plans').then(r => {
        const plans = r.data || []
        if (plans.length > 0) {
          const latest = plans[0]
          let parsed: any = null
          try { parsed = JSON.parse(latest.raw_response) } catch {}
          setLearning(parsed || { priority_weaknesses: latest.focus_areas, suggested_exercises: latest.recommended_exercises, estimated_next_band: latest.target_next_band })
          setLearningIsCached(true)
        }
      }).catch(() => {})
    }
  }, [result?.status, essayId])

  const handleLearn = async () => {
    setLearningLoading(true)
    try {
      const res = await api.post('/learning/analyze')
      setLearning(res.data)
      setLearningIsCached(false)
      setShowLearn(true)
    } catch (e: any) { alert(e.response?.data?.detail || 'Learning analysis failed') }
    finally { setLearningLoading(false) }
  }

  const progress = result?.progress
  const agents = progress?.agents || {}
  const completedAgents = progress?.completed || 0
  const totalAgents = progress?.total || 10
  const pct = totalAgents > 0 ? Math.round((completedAgents / totalAgents) * 100) : 0
  const showProgressPanel = polling && checkedOnce && result?.status !== 'completed' && result?.status !== 'failed'
  const subScores = result?.sub_criteria_scores || {}

  return (
    <div className="max-w-4xl mx-auto space-y-4 pb-12">
      <div className="flex items-center gap-4">
        <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"><ArrowLeft className="w-4 h-4" /> Back</button>
        <h1 className="text-xl font-bold dark:text-white">Scoring Results</h1>
        <div className="flex-1" />
        {result?.status === 'completed' && (
          <button onClick={handleLearn} disabled={learningLoading} className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white rounded-lg font-medium text-sm">
            <Lightbulb className="w-4 h-4" /> {learningLoading ? 'Analyzing...' : learning ? 'Re-analyze' : 'Learn'}
          </button>
        )}
      </div>

      {!checkedOnce && (
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6 text-center text-slate-500">
          Loading...
        </div>
      )}

      {showProgressPanel && (
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
          <div className="flex items-center gap-3 mb-4">
            <RefreshCw className="w-6 h-6 animate-spin text-blue-500" />
            <div>
              <h2 className="font-semibold text-lg dark:text-white">Scoring in Progress</h2>
              <p className="text-sm text-slate-500">{completedAgents} of {totalAgents} agents completed ({pct}%)</p>
            </div>
          </div>
          <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-3 mb-4">
            <div className="h-3 rounded-full bg-blue-500 transition-all duration-500" style={{ width: `${pct}%` }} />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {Object.entries(agents).map(([name, status]: [string, any]) => (
              <div key={name} className="flex items-center gap-2 p-2 rounded-lg bg-slate-50 dark:bg-slate-700/50 text-xs">
                {status.status === 'completed' ? <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0" />
                  : status.status === 'running' ? <RefreshCw className="w-4 h-4 text-blue-500 animate-spin flex-shrink-0" />
                  : status.status === 'failed' ? <XCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
                  : <Clock className="w-4 h-4 text-slate-400 flex-shrink-0" />}
                <span className="text-slate-600 dark:text-slate-400">{AGENT_NAMES[name] || name}</span>
                {status.band != null && <span className="ml-auto font-mono font-bold text-blue-600">{status.band.toFixed(1)}</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      {result?.overall_band != null && !polling && (
        <>
          {/* Overall Band Score */}
          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6 text-center">
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-2">Est. Overall Band Score</p>
            <div className="flex items-center justify-center gap-4">
              <BandBadge score={result.overall_band} />
              <div className="text-left">
                <div className="text-5xl font-bold dark:text-white">{result.overall_band.toFixed(1)}</div>
                <div className="text-sm text-slate-400">(+/- 0.5)</div>
              </div>
            </div>
          </div>

          {/* Criteria Cards */}
          <h2 className="text-lg font-semibold mt-4 dark:text-white">Criterion Breakdown</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {(result?.criteria || []).map((c: any) => {
              const criterionKey = CRITERION_AGENT_MAP[c.criterion] || ''
              return <CriterionCard key={c.criterion} data={c} subScores={subScores[criterionKey]} />
            })}
          </div>

          {/* Band Upgrade */}
          {bandUpgrade?.steps?.length > 0 && (
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-5">
              <h2 className="text-lg font-semibold mb-4 dark:text-white">How to Level Up</h2>
              <div className="space-y-3">
                {bandUpgrade.steps.map((step: any, i: number) => (
                  <div key={i} className="p-4 rounded-lg bg-gradient-to-r from-slate-50 to-blue-50 dark:from-slate-700/50 dark:to-blue-900/20 border border-slate-100 dark:border-slate-700">
                    <h3 className="font-medium text-lg mb-2">To reach <span className="text-blue-600 font-bold">Band {step.target_band}</span></h3>
                    <ul className="list-disc list-inside text-sm text-slate-600 dark:text-slate-400 space-y-1">
                      {step.required_improvements?.map((imp: string, j: number) => <li key={j}>{imp}</li>)}
                    </ul>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Detailed Feedback Section */}
          {feedback && (
            <div className="space-y-4">
              <div className="flex border-b border-slate-200 dark:border-slate-700 gap-1">
                <button
                  onClick={() => setFeedbackTab('analysis')}
                  className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${feedbackTab === 'analysis' ? 'border-blue-500 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400'}`}
                >
                  Detailed Analysis
                </button>
                <button
                  onClick={() => setFeedbackTab('samples')}
                  className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${feedbackTab === 'samples' ? 'border-blue-500 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400'}`}
                >
                  Sample Essays
                </button>
              </div>

              {feedbackTab === 'analysis' && (
                <>
                  {/* Overall Assessment */}
                  {feedback.overall_assessment && (
                    <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-5">
                      <h2 className="text-lg font-semibold mb-3 dark:text-white">Overall Assessment</h2>
                      <p className="text-sm text-slate-600 dark:text-slate-400">{feedback.overall_assessment}</p>
                    </div>
                  )}

                  {/* Paragraph Analysis */}
                  {feedback.paragraph_analysis && feedback.paragraph_analysis.length > 0 && (
                    <CollapsibleSection title="Paragraph-by-Paragraph Analysis" defaultOpen>
                      {feedback.paragraph_analysis.map((pa: PAnalysis, i: number) => (
                        <ParagraphAnalysisCard key={i} pa={pa} />
                      ))}
                    </CollapsibleSection>
                  )}

                  {/* Structure Improvement */}
                  {feedback.structure_improvement && (
                    <CollapsibleSection title={`Essay Structure Guide ${feedback.structure_improvement.task_type ? `— ${feedback.structure_improvement.task_type}` : ''}`}>
                      {feedback.structure_improvement.key_tips?.length > 0 && (
                        <div className="mb-4">
                          <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Key Tips</h4>
                          <ul className="list-disc list-inside text-sm text-slate-600 dark:text-slate-400 space-y-1">
                            {feedback.structure_improvement.key_tips.map((tip: string, i: number) => <li key={i}>{tip}</li>)}
                          </ul>
                        </div>
                      )}
                      {feedback.structure_improvement.recommended_outline?.length > 0 && (
                        <div>
                          <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Recommended Outline</h4>
                          {feedback.structure_improvement.recommended_outline.map((item: { section: string; example_topic_sentence: string }, i: number) => (
                            <div key={i} className="mb-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-100 dark:border-blue-800">
                              <span className="text-xs font-semibold text-blue-700 dark:text-blue-300">{item.section}</span>
                              <p className="text-sm italic text-slate-600 dark:text-slate-400 mt-1">"{item.example_topic_sentence}"</p>
                            </div>
                          ))}
                        </div>
                      )}
                    </CollapsibleSection>
                  )}

                  {/* Vocabulary Table */}
                  {feedback.vocabulary_table && feedback.vocabulary_table.length > 0 && (
                    <CollapsibleSection title="Key Vocabulary">
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b border-slate-200 dark:border-slate-700">
                              <th className="text-left py-2 px-3 font-semibold text-slate-500">Word</th>
                              <th className="text-left py-2 px-3 font-semibold text-slate-500">Type</th>
                              <th className="text-left py-2 px-3 font-semibold text-slate-500">Definition</th>
                            </tr>
                          </thead>
                          <tbody>
                            {feedback.vocabulary_table.map((v: VocabTableItem, i: number) => (
                              <tr key={i} className="border-b border-slate-100 dark:border-slate-700/50">
                                <td className="py-2 px-3 font-medium text-slate-800 dark:text-slate-200">{v.word}</td>
                                <td className="py-2 px-3 text-xs text-slate-500">{v.word_type}</td>
                                <td className="py-2 px-3 text-slate-600 dark:text-slate-400">{v.definition_vn}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </CollapsibleSection>
                  )}

                  {/* Sentence Diversity */}
                  {feedback.sentence_diversity && feedback.sentence_diversity.length > 0 && (
                    <CollapsibleSection title="Sentence Structure Diversity">
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b border-slate-200 dark:border-slate-700">
                              <th className="text-left py-2 px-3 font-semibold text-slate-500">Structure</th>
                              <th className="text-left py-2 px-3 font-semibold text-slate-500">Original</th>
                              <th className="text-left py-2 px-3 font-semibold text-slate-500">Improved</th>
                            </tr>
                          </thead>
                          <tbody>
                            {feedback.sentence_diversity.map((sd: SentenceDiversityItem, i: number) => (
                              <tr key={i} className="border-b border-slate-100 dark:border-slate-700/50">
                                <td className="py-2 px-3 font-medium text-xs text-blue-600 dark:text-blue-400">{sd.grammar_structure}</td>
                                <td className="py-2 px-3 italic text-slate-600 dark:text-slate-400">"{sd.original_sentence}"</td>
                                <td className="py-2 px-3 text-slate-700 dark:text-slate-300">"{sd.rephrased_sentence}"</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </CollapsibleSection>
                  )}

                  {/* Coherence Improvement */}
                  {feedback.coherence_improvement && feedback.coherence_improvement.length > 0 && (
                    <CollapsibleSection title="Coherence & Cohesion Improvements">
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b border-slate-200 dark:border-slate-700">
                              <th className="text-left py-2 px-3 font-semibold text-slate-500">Original</th>
                              <th className="text-left py-2 px-3 font-semibold text-slate-500">Improved</th>
                              <th className="text-left py-2 px-3 font-semibold text-slate-500">Why</th>
                            </tr>
                          </thead>
                          <tbody>
                            {feedback.coherence_improvement.map((ci: CoherenceImprovementItem, i: number) => (
                              <tr key={i} className="border-b border-slate-100 dark:border-slate-700/50">
                                <td className="py-2 px-3 italic text-slate-600 dark:text-slate-400">"{ci.original_text}"</td>
                                <td className="py-2 px-3 text-slate-700 dark:text-slate-300">"{ci.improved_text}"</td>
                                <td className="py-2 px-3 text-xs text-slate-500">{ci.explanation}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </CollapsibleSection>
                  )}

                  {/* Priority & Exercises */}
                  {(feedback.priority_weakness || (feedback.recommended_exercises && feedback.recommended_exercises.length > 0)) && (
                    <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-5">
                      {feedback.priority_weakness && (
                        <div className="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg mb-3 text-sm">
                          <span className="font-medium text-red-600">Priority: </span>
                          <span className="text-slate-600 dark:text-slate-400">{feedback.priority_weakness}</span>
                        </div>
                      )}
                      {feedback.recommended_exercises && feedback.recommended_exercises.length > 0 && (
                        <div>
                          <span className="text-xs font-semibold text-slate-500 uppercase">Recommended Exercises</span>
                          <ul className="list-decimal list-inside text-sm text-slate-600 dark:text-slate-400 mt-1 space-y-1">
                            {feedback.recommended_exercises.map((ex: string, i: number) => <li key={i}>{ex}</li>)}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}

              {feedbackTab === 'samples' && (
                <>
                  {feedback.sample_essays?.corrected_essay && (
                    <CollapsibleSection title="Corrected Essay (Band 5.5–6.5)" defaultOpen>
                      <p className="text-sm text-slate-600 dark:text-slate-400 whitespace-pre-wrap leading-relaxed">{feedback.sample_essays.corrected_essay}</p>
                    </CollapsibleSection>
                  )}
                  {feedback.sample_essays?.model_essay_band_8_9 && (
                    <CollapsibleSection title="Model Essay (Band 8.0–9.0)" defaultOpen>
                      <p className="text-sm text-slate-600 dark:text-slate-400 whitespace-pre-wrap leading-relaxed">{feedback.sample_essays.model_essay_band_8_9}</p>
                    </CollapsibleSection>
                  )}
                </>
              )}
            </div>
          )}

          {/* Criterion Feedback (fallback if no comprehensive feedback) */}
          {feedback?.criterion_feedback && !feedback.paragraph_analysis && Object.keys(feedback.criterion_feedback).length > 0 && (
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-5">
              <h2 className="text-lg font-semibold mb-3 dark:text-white">Per-Criterion Feedback</h2>
              <div className="space-y-3">
                {Object.entries(feedback.criterion_feedback).map(([key, val]) => (
                  <div key={key} className="p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg">
                    <span className="text-xs font-semibold uppercase text-slate-500">{CRITERION_LABELS[key] || key}</span>
                    <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">{val as string}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Errors */}
          {errors.length > 0 && (
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-5">
              <h2 className="text-lg font-semibold mb-4 dark:text-white">Errors Found ({errors.length})</h2>
              <div className="space-y-2">
                {errors.map((err: any, i: number) => (
                  <div key={i} className="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-100 dark:border-red-800">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <span className="text-xs px-2 py-0.5 rounded-full bg-red-100 dark:bg-red-800 text-red-700 dark:text-red-300">{err.error_type}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${err.severity === 'severe' ? 'bg-red-200 text-red-800' : err.severity === 'moderate' ? 'bg-orange-100 text-orange-700' : 'bg-yellow-100 text-yellow-700'}`}>{err.severity}</span>
                    </div>
                    <p className="text-sm"><span className="line-through text-red-500">{err.error_text}</span> {err.correction && <span className="text-green-600 font-medium">→ {err.correction}</span>}</p>
                    {err.explanation && <p className="text-xs text-slate-500 mt-1">{err.explanation}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Vocabulary */}
          {vocab.length > 0 && (
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-5">
              <h2 className="text-lg font-semibold mb-4 dark:text-white">Extracted Vocabulary ({vocab.length} words)</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {vocab.slice(0, 20).map((v: any, i: number) => (
                  <div key={i} className="p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg text-sm">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{v.word}</span>
                      <span className="text-xs text-slate-400">{v.pos} {v.cefr_level && `· ${v.cefr_level}`}</span>
                    </div>
                    {v.definition && <p className="text-xs text-slate-500 mt-0.5">{v.definition}</p>}
                    {v.ipa && <p className="text-xs text-slate-400">/{v.ipa}/</p>}
                    {v.example_sentence && <p className="text-xs text-slate-400 italic mt-0.5">"{v.example_sentence}"</p>}
                    {v.synonyms?.length > 0 && <p className="text-xs text-blue-500 mt-0.5">syn: {v.synonyms.join(', ')}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* Learning Modal */}
      {(showLearn || learningIsCached) && learning && (
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-green-800 dark:text-green-300">
              Personalized Learning Plan {learningIsCached && <span className="text-xs font-normal text-green-600">(saved)</span>}
            </h2>
            <button onClick={() => { setShowLearn(false); setLearningIsCached(false) }} className="text-green-600 hover:text-green-800">×</button>
          </div>
          {learning.recurring_mistakes?.length > 0 && (
            <div className="mb-4">
              <h3 className="font-medium text-sm text-green-700 mb-2">Recurring Mistakes</h3>
              <div className="space-y-2">
                {learning.recurring_mistakes.map((m: any, i: number) => (
                  <div key={i} className="p-3 bg-white dark:bg-slate-800 rounded-lg">
                    <span className="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700">{m.type}</span>
                    <span className="ml-2 text-xs text-slate-500">{m.frequency}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          {learning.hidden_patterns?.length > 0 && (
            <div className="mb-4">
              <h3 className="font-medium text-sm text-green-700 mb-2">Hidden Patterns</h3>
              <ul className="list-disc list-inside text-sm text-slate-600 dark:text-slate-400">{learning.hidden_patterns.map((p: string, i: number) => <li key={i}>{p}</li>)}</ul>
            </div>
          )}
          {learning.priority_weaknesses?.length > 0 && (
            <div className="mb-4">
              <h3 className="font-medium text-sm text-green-700 mb-2">Priority Areas</h3>
              {learning.priority_weaknesses.map((w: any, i: number) => (
                <div key={i} className="flex items-center gap-2 text-sm mb-1">
                  <span className={`w-2 h-2 rounded-full ${w.severity === 'high' ? 'bg-red-500' : w.severity === 'medium' ? 'bg-amber-500' : 'bg-blue-500'}`} />
                  <span className="text-slate-600 dark:text-slate-400">{w.criterion}: {w.description}</span>
                </div>
              ))}
            </div>
          )}
          {learning.suggested_exercises?.length > 0 && (
            <div className="mb-4">
              <h3 className="font-medium text-sm text-green-700 mb-2">Suggested Exercises</h3>
              <ol className="list-decimal list-inside text-sm text-slate-600 dark:text-slate-400">{learning.suggested_exercises.map((ex: string, i: number) => <li key={i}>{ex}</li>)}</ol>
            </div>
          )}
          {learning.estimated_next_band && (
            <div className="text-center p-3 bg-green-100 dark:bg-green-800/30 rounded-lg">
              <span className="text-sm text-green-700">Estimated next band: </span>
              <span className="font-bold text-green-800 text-xl">{learning.estimated_next_band.toFixed(1)}</span>
            </div>
          )}
        </div>
      )}

      {result?.status === 'failed' && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6 text-center">
          <XCircle className="w-10 h-10 mx-auto mb-2 text-red-500" />
          <p className="text-red-600 mb-4">Scoring failed. Check your API key in Settings, then edit and retry.</p>
          <button onClick={() => navigate(`/essay/${essayId}/edit`)} className="inline-flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium text-sm">
            <Pencil className="w-4 h-4" /> Edit & Retry
          </button>
        </div>
      )}
    </div>
  )
}
