import { useState, useEffect } from 'react'
import api from '../lib/api'
import { Download } from 'lucide-react'

export default function VocabularyPage() {
  const [data, setData] = useState<any>(null)
  const [cefrFilter, setCefrFilter] = useState('')
  const [exporting, setExporting] = useState<'csv' | 'excel' | null>(null)

  useEffect(() => {
    const params: any = { page: 1, page_size: 50 }
    if (cefrFilter) params.cefr_level = cefrFilter
    api.get('/vocabulary', { params }).then(r => setData(r.data))
  }, [cefrFilter])

  const handleExport = async (format: 'csv' | 'excel') => {
    setExporting(format)
    try {
      const res = await api.post('/vocabulary/export', null, { params: { format }, responseType: 'blob' })
      const url = URL.createObjectURL(res.data)
      const a = document.createElement('a')
      a.href = url
      a.download = format === 'csv' ? 'vocabulary.csv' : 'vocabulary.xlsx'
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    } catch (e: any) {
      alert('Export failed. Please try again.')
    } finally {
      setExporting(null)
    }
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Vocabulary Bank</h1>
        <div className="flex items-center gap-2">
          <select value={cefrFilter} onChange={e => setCefrFilter(e.target.value)} className="px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-sm">
            <option value="">All Levels</option>
            <option value="A1">A1</option>
            <option value="A2">A2</option>
            <option value="B1">B1</option>
            <option value="B2">B2</option>
            <option value="C1">C1</option>
            <option value="C2">C2</option>
          </select>
          <button onClick={() => handleExport('csv')} disabled={exporting !== null} className="flex items-center gap-1 px-3 py-2 text-sm border rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 disabled:opacity-50">
            <Download className="w-4 h-4" /> {exporting === 'csv' ? 'Exporting...' : 'CSV'}
          </button>
          <button onClick={() => handleExport('excel')} disabled={exporting !== null} className="flex items-center gap-1 px-3 py-2 text-sm border rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 disabled:opacity-50">
            <Download className="w-4 h-4" /> {exporting === 'excel' ? 'Exporting...' : 'Excel'}
          </button>
        </div>
      </div>

      {data?.stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border p-4 text-center">
            <div className="text-2xl font-bold text-blue-600">{data.stats.total_unique}</div>
            <div className="text-xs text-slate-500">Total Words</div>
          </div>
          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border p-4 text-center">
            <div className="text-2xl font-bold text-green-600">{data.stats.academic_count}</div>
            <div className="text-xs text-slate-500">Academic</div>
          </div>
          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border p-4 text-center">
            <div className="text-2xl font-bold text-purple-600">{(data.stats.by_cefr?.['B2'] || 0) + (data.stats.by_cefr?.['C1'] || 0) + (data.stats.by_cefr?.['C2'] || 0)}</div>
            <div className="text-xs text-slate-500">B2-C2</div>
          </div>
          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border p-4 text-center">
            <div className="text-2xl font-bold text-red-500">{data.stats.error_count}</div>
            <div className="text-xs text-slate-500">Usage Issues</div>
          </div>
        </div>
      )}

      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border">
        {data?.items?.map((item: any, i: number) => (
          <div key={item.id || i} className="px-5 py-3 border-b border-slate-100 dark:border-slate-700 text-sm hover:bg-slate-50 dark:hover:bg-slate-750">
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-semibold text-base">{item.word}</span>
                  {item.ipa && <span className="text-xs text-slate-400 font-mono">/{item.ipa}/</span>}
                  {item.pos && <span className="text-xs text-slate-500 italic">{item.pos}</span>}
                  {item.cefr_level && (
                    <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${
                      item.cefr_level === 'C1' || item.cefr_level === 'C2' ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300' :
                      item.cefr_level === 'B1' || item.cefr_level === 'B2' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300' :
                      'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-400'
                    }`}>{item.cefr_level}</span>
                  )}
                  {item.is_academic && <span className="text-xs px-1.5 py-0.5 rounded bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300">Academic</span>}
                </div>
                {item.definition && <p className="text-xs text-slate-500 mt-0.5">{item.definition}</p>}
                {item.example_sentence && <p className="text-xs text-slate-400 italic mt-0.5">"{item.example_sentence}"</p>}
                {item.synonyms?.length > 0 && (
                  <div className="flex gap-1 mt-1 flex-wrap">
                    {item.synonyms.map((s: string, j: number) => <span key={j} className="text-xs px-1.5 py-0.5 rounded bg-blue-50 dark:bg-blue-900/20 text-blue-600">{s}</span>)}
                  </div>
                )}
                {item.context_sentence && <p className="text-xs text-slate-400 mt-1">From essay: "{item.context_sentence}"</p>}
              </div>
              {item.usage_accuracy != null && (
                <span className={`text-xs px-2 py-1 rounded-full font-medium flex-shrink-0 ${
                  item.usage_accuracy >= 0.8 ? 'bg-green-100 text-green-700' :
                  item.usage_accuracy >= 0.5 ? 'bg-amber-100 text-amber-700' :
                  'bg-red-100 text-red-700'
                }`}>{(item.usage_accuracy * 100).toFixed(0)}%</span>
              )}
            </div>
          </div>
        ))}
        {!data?.items?.length && (
          <div className="p-8 text-center text-slate-500">No vocabulary extracted yet. Score an essay to build your vocabulary bank.</div>
        )}
      </div>
    </div>
  )
}
