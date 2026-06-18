import { useState, useRef, useEffect, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import api from '../lib/api'
import { Timer, Pause, Play, RotateCcw, Send, Lightbulb, ImagePlus, X, Upload } from 'lucide-react'

export default function NewEssay() {
  const navigate = useNavigate()
  const { essayId } = useParams<{ essayId?: string }>()
  const isEditMode = !!essayId

  const [taskType, setTaskType] = useState<'task1' | 'task2'>('task2')
  const [essayText, setEssayText] = useState('')
  const [promptText, setPromptText] = useState('')
  const [examLabel, setExamLabel] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [loadingExisting, setLoadingExisting] = useState(isEditMode)

  // Image upload for Task 1
  const [image, setImage] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [existingImageUrl, setExistingImageUrl] = useState<string | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Pre-writing assistant
  const [preWriting, setPreWriting] = useState(false)
  const [preWritingResult, setPreWritingResult] = useState<any>(null)
  const [showPreWriting, setShowPreWriting] = useState(false)

  // Timer
  const [timerSeconds, setTimerSeconds] = useState(40 * 60)
  const [timerRunning, setTimerRunning] = useState(false)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const [timerMode, setTimerMode] = useState<'full' | 'custom'>('full')
  const [customMinutes, setCustomMinutes] = useState(40)

  useEffect(() => {
    setTimerSeconds(taskType === 'task1' ? 20 * 60 : 40 * 60)
    setCustomMinutes(taskType === 'task1' ? 20 : 40)
  }, [taskType])

  useEffect(() => {
    if (timerRunning && timerSeconds > 0) {
      timerRef.current = setInterval(() => setTimerSeconds(s => s - 1), 1000)
    } else if (timerSeconds === 0) {
      setTimerRunning(false)
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [timerRunning, timerSeconds])

  // Load the existing essay when editing
  useEffect(() => {
    if (!essayId) return
    api.get(`/essays/${essayId}`).then(r => {
      const e = r.data
      if (e.status !== 'pending' && e.status !== 'failed') {
        alert('This essay has already been scored and can no longer be edited.')
        navigate(`/essay/${essayId}`)
        return
      }
      setTaskType(e.task_type)
      setEssayText(e.essay_text || '')
      setPromptText(e.prompt_text || '')
      setExamLabel(e.exam_label || '')
      if (e.image_path) {
        const filename = e.image_path.split('/').pop()
        setExistingImageUrl(`/uploads/${filename}`)
      }
      setLoadingExisting(false)
    }).catch(() => {
      alert('Could not load essay to edit.')
      navigate('/essays')
    })
  }, [essayId, navigate])

  // Auto-save (only for new essays — edits load their own state from the server)
  useEffect(() => {
    if (isEditMode || !essayText) return
    const t = setTimeout(() => {
      localStorage.setItem('draft_essay', JSON.stringify({ taskType, essayText, promptText, examLabel, timestamp: Date.now() }))
    }, 2000)
    return () => clearTimeout(t)
  }, [essayText, taskType, promptText, examLabel, isEditMode])

  // Load draft (only for new essays)
  useEffect(() => {
    if (isEditMode) return
    const draft = localStorage.getItem('draft_essay')
    if (draft) {
      try {
        const d = JSON.parse(draft)
        if (d.essayText) { setTaskType(d.taskType || 'task2'); setEssayText(d.essayText); setPromptText(d.promptText || ''); setExamLabel(d.examLabel || '') }
      } catch {}
    }
  }, [isEditMode])

  const wordCount = essayText.trim() ? essayText.trim().split(/\s+/).length : 0
  const charCount = essayText.length
  const paragraphs = essayText.trim() ? essayText.split(/\n\n+/).filter(p => p.trim()).length : 0

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60)
    const sec = s % 60
    return `${m}:${sec.toString().padStart(2, '0')}`
  }

  const handleImageDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file && file.type.startsWith('image/')) {
      setImage(file)
      setImagePreview(URL.createObjectURL(file))
      setExistingImageUrl(null)
    }
  }

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) { setImage(file); setImagePreview(URL.createObjectURL(file)); setExistingImageUrl(null) }
  }

  const handlePreWriting = async () => {
    if (!promptText.trim()) return
    setPreWriting(true)
    setShowPreWriting(true)
    try {
      const res = await api.post('/learning/pre-write', { task_type: taskType, prompt_text: promptText })
      setPreWritingResult(res.data)
    } catch (e: any) { alert(e.response?.data?.detail || 'Pre-writing failed') }
    setPreWriting(false)
  }

  const handleSubmit = useCallback(async () => {
    if (!essayText.trim()) return
    setSubmitting(true)
    try {
      let res
      const useMultipart = taskType === 'task1' && (image || isEditMode)
      if (useMultipart) {
        const formData = new FormData()
        formData.append('essay_text', essayText)
        if (promptText) formData.append('prompt_text', promptText)
        if (examLabel) formData.append('exam_label', examLabel)
        if (image) formData.append('image', image)
        const url = isEditMode ? `/essays/${essayId}/task1` : '/essays/task1'
        res = await api[isEditMode ? 'patch' : 'post'](url, formData, { headers: { 'Content-Type': 'multipart/form-data' } })
      } else if (isEditMode) {
        res = await api.patch(`/essays/${essayId}`, { essay_text: essayText, prompt_text: promptText || undefined, exam_label: examLabel || undefined })
      } else {
        res = await api.post('/essays', { task_type: taskType, essay_text: essayText, prompt_text: promptText || undefined, exam_label: examLabel || undefined })
      }
      localStorage.removeItem('draft_essay')
      await api.post(`/essays/${res.data.id}/score`)
      navigate(`/essay/${res.data.id}`)
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Submission failed')
    } finally { setSubmitting(false) }
  }, [essayText, taskType, promptText, examLabel, image, isEditMode, essayId, navigate])

  if (loadingExisting) {
    return <div className="max-w-4xl mx-auto p-8 text-center text-slate-500">Loading essay...</div>
  }

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{isEditMode ? 'Edit Essay' : 'New Essay'}</h1>
        <div className="flex items-center gap-3">
          <select value={taskType} disabled={isEditMode} onChange={e => { setTaskType(e.target.value as any); setImage(null); setImagePreview(null) }} className="px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-sm disabled:opacity-60">
            <option value="task2">Task 2</option>
            <option value="task1">Task 1</option>
          </select>
          <button onClick={handlePreWriting} disabled={preWriting || !promptText.trim()} className="flex items-center gap-2 px-4 py-2 bg-amber-500 hover:bg-amber-600 disabled:opacity-50 text-white rounded-lg font-medium text-sm">
            <Lightbulb className="w-4 h-4" /> {preWriting ? 'Analyzing...' : 'Pre-Writing'}
          </button>
        </div>
      </div>

      {isEditMode && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg px-4 py-2 text-sm text-blue-700 dark:text-blue-300">
          Editing a not-yet-scored essay. Saving will resubmit it for scoring.
        </div>
      )}

      {/* Pre-Writing Result */}
      {showPreWriting && preWritingResult && (
        <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-amber-800 dark:text-amber-300">Pre-Writing Analysis</h3>
            <button onClick={() => setShowPreWriting(false)} className="text-amber-600 hover:text-amber-800"><X className="w-4 h-4" /></button>
          </div>
          <div className="space-y-3 text-sm">
            {taskType === 'task1' ? (
              <>
                <div><span className="font-medium text-amber-700">Type:</span> <span className="capitalize">{preWritingResult.chart_type || preWritingResult.task_type}</span></div>
                {preWritingResult.key_trends && <div><span className="font-medium text-amber-700">Key Trends:</span> <p className="text-slate-600 dark:text-slate-400 mt-1">{preWritingResult.key_trends}</p></div>}
                {preWritingResult.suggested_overview && <div><span className="font-medium text-amber-700">Suggested Overview:</span> <p className="text-slate-600 dark:text-slate-400 mt-1">{preWritingResult.suggested_overview}</p></div>}
                {preWritingResult.suggested_paragraph_structure && <div><span className="font-medium text-amber-700">Paragraph Structure:</span> <p className="text-slate-600 dark:text-slate-400 mt-1">{preWritingResult.suggested_paragraph_structure}</p></div>}
              </>
            ) : (
              <>
                <div><span className="font-medium text-amber-700">Essay Type:</span> <span className="capitalize">{(preWritingResult.essay_type || '').replace(/_/g, ' ')}</span></div>
                {preWritingResult.question_analysis && <div><span className="font-medium text-amber-700">Analysis:</span> <p className="text-slate-600 dark:text-slate-400 mt-1">{preWritingResult.question_analysis}</p></div>}
                {preWritingResult.brainstorming_ideas?.length > 0 && (
                  <div>
                    <span className="font-medium text-amber-700">Ideas:</span>
                    <ul className="list-disc list-inside text-slate-600 dark:text-slate-400 mt-1">{preWritingResult.brainstorming_ideas.map((idea: string, i: number) => <li key={i}>{idea}</li>)}</ul>
                  </div>
                )}
                {preWritingResult.suggested_structure && <div><span className="font-medium text-amber-700">Structure:</span> <p className="text-slate-600 dark:text-slate-400 mt-1">{preWritingResult.suggested_structure}</p></div>}
              </>
            )}
            {preWritingResult.common_mistakes?.length > 0 && (
              <div>
                <span className="font-medium text-amber-700">Common Mistakes:</span>
                <ul className="list-disc list-inside text-slate-600 dark:text-slate-400 mt-1">{preWritingResult.common_mistakes.map((m: string, i: number) => <li key={i}>{m}</li>)}</ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Timer */}
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className={`text-2xl font-mono font-bold ${timerSeconds < 60 ? 'text-red-500 animate-pulse' : ''}`}>{formatTime(timerSeconds)}</span>
            {timerSeconds === 0 && (
              <span className="text-sm font-medium px-3 py-1 rounded-full bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300">
                ⏰ Time's up! You can keep writing or submit now.
              </span>
            )}
            <div className="flex gap-1">
              <button onClick={() => setTimerRunning(!timerRunning)} className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700">
                {timerRunning ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              </button>
              <button onClick={() => { setTimerRunning(false); setTimerSeconds(taskType === 'task1' ? 20 * 60 : 40 * 60) }} className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700">
                <RotateCcw className="w-4 h-4" />
              </button>
            </div>
            <select value={timerMode} onChange={e => { setTimerMode(e.target.value as any); if (e.target.value === 'custom') setTimerSeconds(customMinutes * 60) }} className="px-2 py-1 text-sm border rounded dark:bg-slate-700 dark:border-slate-600">
              <option value="full">Full Test ({taskType === 'task1' ? 20 : 40}m)</option>
              <option value="custom">Custom</option>
            </select>
            {timerMode === 'custom' && (
              <input type="number" value={customMinutes} onChange={e => { const v = parseInt(e.target.value) || 1; setCustomMinutes(v); setTimerSeconds(v * 60) }} className="w-16 px-2 py-1 text-sm border rounded dark:bg-slate-700 dark:border-slate-600" min={1} />
            )}
          </div>
          <button onClick={handleSubmit} disabled={submitting || !essayText.trim()} className="flex items-center gap-2 px-5 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg font-medium">
            <Send className="w-4 h-4" /> {submitting ? 'Submitting...' : isEditMode ? 'Save & Score' : 'Submit & Score'}
          </button>
        </div>
      </div>

      {/* Exam / attempt label */}
      <div>
        <label className="block text-sm font-medium mb-1 text-slate-600 dark:text-slate-400">Exam / Attempt Label (optional)</label>
        <input
          type="text"
          value={examLabel}
          onChange={e => setExamLabel(e.target.value)}
          placeholder="e.g. Mock Test 1, Cambridge Book 17 Test 3..."
          className="w-full px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-sm"
        />
        <p className="text-xs text-slate-400 mt-1">Group related submissions together for easier browsing in History.</p>
      </div>

      {/* Prompt */}
      <div>
        <label className="block text-sm font-medium mb-1 text-slate-600 dark:text-slate-400">Writing Prompt</label>
        <textarea value={promptText} onChange={e => setPromptText(e.target.value)} placeholder="Paste the IELTS writing prompt here..." className="w-full px-4 py-3 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 min-h-[80px] resize-y text-sm" />
      </div>

      {/* Image Upload (Task 1 only) */}
      {taskType === 'task1' && (
        <div>
          <label className="block text-sm font-medium mb-1 text-slate-600 dark:text-slate-400">Chart/Graph Image</label>
          {imagePreview || existingImageUrl ? (
            <div className="relative inline-block">
              <img src={imagePreview || existingImageUrl || ''} alt="Preview" className="max-h-60 rounded-lg border border-slate-200 dark:border-slate-700" />
              <button onClick={() => { setImage(null); setImagePreview(null); setExistingImageUrl(null) }} className="absolute top-2 right-2 p-1 bg-red-500 text-white rounded-full"><X className="w-3 h-3" /></button>
            </div>
          ) : (
            <div
              onDragOver={e => { e.preventDefault(); setDragOver(true) }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleImageDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${dragOver ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-slate-300 dark:border-slate-600 hover:border-blue-400'}`}
            >
              <Upload className="w-8 h-8 mx-auto mb-2 text-slate-400" />
              <p className="text-sm text-slate-500">Drag and drop a chart image here, or click to browse</p>
              <p className="text-xs text-slate-400 mt-1">Supports: PNG, JPG, GIF</p>
              <input ref={fileInputRef} type="file" accept="image/*" onChange={handleImageSelect} className="hidden" />
            </div>
          )}
        </div>
      )}

      {/* Editor */}
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700">
        <textarea
          value={essayText}
          onChange={e => setEssayText(e.target.value)}
          placeholder="Write your essay here...&#10;&#10;Use double line breaks for new paragraphs."
          className="w-full px-6 py-5 bg-transparent min-h-[400px] resize-y focus:outline-none text-base leading-relaxed"
          autoFocus
        />
        <div className="flex items-center gap-6 px-6 py-3 border-t border-slate-200 dark:border-slate-700 text-sm text-slate-500">
          <span>Words: <strong className={wordCount < (taskType === 'task1' ? 150 : 250) ? 'text-red-500' : 'text-green-600'}>{wordCount}</strong> (min {taskType === 'task1' ? 150 : 250})</span>
          <span>Characters: <strong>{charCount}</strong></span>
          <span>Paragraphs: <strong>{paragraphs}</strong></span>
          <span className="ml-auto text-xs text-slate-400">{isEditMode ? '' : 'Auto-save enabled'}</span>
        </div>
      </div>
    </div>
  )
}
