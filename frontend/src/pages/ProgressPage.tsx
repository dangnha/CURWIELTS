import { useState, useEffect } from 'react'
import api from '../lib/api'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

export default function ProgressPage() {
  const [progress, setProgress] = useState<any>(null)

  useEffect(() => { api.get('/learning/progress').then(r => setProgress(r.data)) }, [])

  const TrendIcon = progress?.trend === 'improving' ? TrendingUp : progress?.trend === 'declining' ? TrendingDown : Minus
  const trendColor = progress?.trend === 'improving' ? 'text-green-500' : progress?.trend === 'declining' ? 'text-red-500' : 'text-slate-400'

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Progress Tracking</h1>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border p-4 text-center">
          <TrendIcon className={`w-8 h-8 mx-auto mb-1 ${trendColor}`} />
          <div className="text-xl font-bold capitalize">{progress?.trend || 'No data'}</div>
          <div className="text-xs text-slate-500">Trend</div>
        </div>
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border p-4 text-center">
          <div className="text-xl font-bold text-green-600">{progress?.strongest_criterion || '-'}</div>
          <div className="text-xs text-slate-500">Strongest</div>
        </div>
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border p-4 text-center">
          <div className="text-xl font-bold text-red-500">{progress?.weakest_criterion || '-'}</div>
          <div className="text-xs text-slate-500">Weakest</div>
        </div>
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border p-4 text-center">
          <div className="text-xl font-bold">{progress?.estimated_next_band?.toFixed(1) || '-'}</div>
          <div className="text-xs text-slate-500">Est. Next Band</div>
        </div>
      </div>

      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border p-5">
        <h2 className="font-semibold mb-4">Band Score History</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-700 text-slate-500 text-left">
                <th className="py-2">Date</th>
                <th className="py-2 text-right">Overall</th>
                <th className="py-2 text-right">Task Resp.</th>
                <th className="py-2 text-right">Coh&Cohes</th>
                <th className="py-2 text-right">Lexical</th>
                <th className="py-2 text-right">Grammar</th>
              </tr>
            </thead>
            <tbody>
              {progress?.points?.map((p: any, i: number) => {
                const scores = [p.task_response, p.coherence_cohesion, p.lexical_resource, p.grammatical_range].filter(s => s != null)
                const minScore = scores.length ? Math.min(...scores) : 0
                const maxScore = scores.length ? Math.max(...scores) : 9
                return (
                  <tr key={i} className="border-b border-slate-100 dark:border-slate-700">
                    <td className="py-2">{p.date || `#${i + 1}`}</td>
                    <td className="py-2 text-right">
                      <span className={`font-mono font-bold text-base ${(p.overall_band || 0) >= 7 ? 'text-green-600' : (p.overall_band || 0) >= 6 ? 'text-amber-600' : 'text-red-500'}`}>
                        {p.overall_band?.toFixed(1) || '-'}
                      </span>
                    </td>
                    <td className="py-2 text-right">
                      <span className={`font-mono ${p.task_response === minScore ? 'text-red-400' : p.task_response === maxScore ? 'text-green-500' : ''}`}>
                        {p.task_response?.toFixed(1) || '-'}
                      </span>
                    </td>
                    <td className="py-2 text-right">
                      <span className={`font-mono ${p.coherence_cohesion === minScore ? 'text-red-400' : p.coherence_cohesion === maxScore ? 'text-green-500' : ''}`}>
                        {p.coherence_cohesion?.toFixed(1) || '-'}
                      </span>
                    </td>
                    <td className="py-2 text-right">
                      <span className={`font-mono ${p.lexical_resource === minScore ? 'text-red-400' : p.lexical_resource === maxScore ? 'text-green-500' : ''}`}>
                        {p.lexical_resource?.toFixed(1) || '-'}
                      </span>
                    </td>
                    <td className="py-2 text-right">
                      <span className={`font-mono ${p.grammatical_range === minScore ? 'text-red-400' : p.grammatical_range === maxScore ? 'text-green-500' : ''}`}>
                        {p.grammatical_range?.toFixed(1) || '-'}
                      </span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          {!progress?.points?.length && <div className="p-8 text-center text-slate-500">No scored essays yet.</div>}
        </div>
      </div>
    </div>
  )
}
