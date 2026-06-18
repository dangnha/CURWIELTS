import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../lib/api'
import { PenLine, TrendingUp, FileText, BarChart3, Lightbulb } from 'lucide-react'

export default function Dashboard() {
  const navigate = useNavigate()
  const [essays, setEssays] = useState<any>(null)
  const [stats, setStats] = useState<any>(null)
  const [learning, setLearning] = useState<any>(null)
  const [learnLoading, setLearnLoading] = useState(false)

  const token = localStorage.getItem('token')

  useEffect(() => {
    if (!token) return
    api.get('/essays?page=1&page_size=5').then(r => setEssays(r.data))
    api.get('/users/me/stats').then(r => setStats(r.data))
    // Show the most recent saved learning plan, if any, instead of
    // forcing a fresh (paid) LLM call just to view it on every visit.
    api.get('/learning/plans').then(r => {
      const plans = r.data || []
      if (plans.length === 0) return
      const latest = plans[0]
      let parsed: any = null
      try { parsed = JSON.parse(latest.raw_response) } catch {}
      setLearning(parsed || { priority_weaknesses: latest.focus_areas, suggested_exercises: latest.recommended_exercises, estimated_next_band: latest.target_next_band })
    }).catch(() => {})
  }, [token])

  const handleLearn = async () => {
    setLearnLoading(true)
    try {
      const res = await api.post('/learning/analyze')
      setLearning(res.data)
    } catch (e: any) { alert(e.response?.data?.detail || 'Learning analysis failed') }
    setLearnLoading(false)
  }

  // Auth
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isRegister, setIsRegister] = useState(false)
  const [error, setError] = useState('')

  const handleAuth = async () => {
    try {
      setError('')
      const endpoint = isRegister ? '/auth/register' : '/auth/login'
      const res = await api.post(endpoint, { username, password })
      if (res.data.access_token) {
        localStorage.setItem('token', res.data.access_token)
        window.location.reload()
      }
    } catch (e: any) { setError(e.response?.data?.detail || 'Authentication failed') }
  }

  if (!token) {
    return (
      <div className="max-w-md mx-auto mt-20">
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-8">
          <h1 className="text-2xl font-bold mb-2 text-center">IELTS Writing Scorer</h1>
          <p className="text-sm text-slate-500 text-center mb-6">AI-powered essay evaluation with multi-agent scoring</p>
          <div className="space-y-3">
            <input type="text" placeholder="Username" value={username} onChange={e => setUsername(e.target.value)}
              className="w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700" />
            <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleAuth()}
              className="w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700" />
            {error && <p className="text-red-500 text-sm">{error}</p>}
            <button onClick={handleAuth} className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium">
              {isRegister ? 'Register' : 'Login'}
            </button>
            <button onClick={() => setIsRegister(!isRegister)} className="w-full text-sm text-blue-600 hover:underline">
              {isRegister ? 'Already have an account? Login' : "Don't have an account? Register"}
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <div className="flex gap-2">
          <button onClick={handleLearn} disabled={learnLoading}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white rounded-lg font-medium text-sm">
            <Lightbulb className="w-4 h-4" /> {learnLoading ? 'Analyzing...' : learning ? 'Re-analyze' : 'Learn'}
          </button>
          <button onClick={() => navigate('/new-essay')}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium text-sm">
            <PenLine className="w-4 h-4" /> New Essay
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-5">
          <FileText className="w-8 h-8 text-blue-500 mb-2" />
          <div className="text-3xl font-bold">{stats?.total_essays || 0}</div>
          <div className="text-sm text-slate-500">Total Essays</div>
        </div>
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-5">
          <TrendingUp className="w-8 h-8 text-green-500 mb-2" />
          <div className="text-3xl font-bold">{stats?.scored_essays || 0}</div>
          <div className="text-sm text-slate-500">Scored</div>
        </div>
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-5">
          <span className="text-3xl font-bold text-blue-600">{stats?.latest_band?.toFixed(1) || '-'}</span>
          <div className="text-sm text-slate-500">Latest Band</div>
        </div>
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-5">
          <BarChart3 className="w-8 h-8 text-purple-500 mb-2" />
          <div className="text-3xl font-bold">{stats?.target_band?.toFixed(1) || '-'}</div>
          <div className="text-sm text-slate-500">Target Band</div>
        </div>
      </div>

      {/* Learning Result */}
      {learning && (
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl p-5">
          <h2 className="font-semibold text-green-800 dark:text-green-300 mb-3">Learning Insights</h2>
          {learning.recurring_mistakes?.length > 0 && (
            <div className="mb-3">
              <span className="text-xs font-medium text-green-700">Recurring Mistakes:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {learning.recurring_mistakes.map((m: any, i: number) => (
                  <span key={i} className="text-xs px-2 py-0.5 rounded-full bg-white dark:bg-slate-800 border border-red-200 text-red-700">
                    {m.type} ({m.frequency})
                  </span>
                ))}
              </div>
            </div>
          )}
          {learning.priority_weaknesses?.length > 0 && (
            <div>
              <span className="text-xs font-medium text-green-700">Priority Areas:</span>
              {learning.priority_weaknesses.map((w: any, i: number) => (
                <div key={i} className="flex items-center gap-2 text-sm mt-1">
                  <span className={`w-2 h-2 rounded-full ${w.severity === 'high' ? 'bg-red-500' : w.severity === 'medium' ? 'bg-amber-500' : 'bg-blue-500'}`} />
                  <span className="text-slate-600 dark:text-slate-400">{w.criterion}: {w.description}</span>
                </div>
              ))}
            </div>
          )}
          {learning.estimated_next_band && (
            <p className="mt-3 text-sm">
              <span className="text-green-700">Estimated next band: </span>
              <span className="font-bold text-green-800">{learning.estimated_next_band.toFixed(1)}</span>
            </p>
          )}
        </div>
      )}

      {/* Recent Essays */}
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700">
        <div className="px-5 py-4 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
          <h2 className="font-semibold">Recent Essays</h2>
          <button onClick={() => navigate('/essays')} className="text-sm text-blue-600 hover:underline">View all</button>
        </div>
        {essays?.items?.length === 0 && (
          <div className="p-8 text-center text-slate-500">
            No essays yet.{' '}
            <button onClick={() => navigate('/new-essay')} className="text-blue-600 hover:underline">Write your first essay</button>
          </div>
        )}
        {essays?.items?.map((essay: any) => (
          <div key={essay.id} onClick={() => navigate(`/essay/${essay.id}`)}
            className="px-5 py-3 border-b border-slate-100 dark:border-slate-700 last:border-0 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-750">
            <div className="flex items-center justify-between">
              <div>
                <span className="font-medium">{essay.task_type?.toUpperCase()}</span>
                <span className="ml-2 text-sm text-slate-500">{essay.word_count} words</span>
                {essay.essay_type && <span className="ml-2 text-xs text-slate-400 capitalize">{essay.essay_type.replace(/_/g, ' ')}</span>}
              </div>
              <span className={`text-xs px-2 py-0.5 rounded-full ${
                essay.status === 'completed' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300' :
                essay.status === 'processing' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300' :
                essay.status === 'failed' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300' :
                'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-400'
              }`}>{essay.status}</span>
            </div>
            <p className="text-sm text-slate-500 mt-1 truncate">{essay.essay_text.slice(0, 120)}...</p>
          </div>
        ))}
      </div>
    </div>
  )
}
