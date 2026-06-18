import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../lib/api'
import { Trash2, ChevronLeft, ChevronRight, Pencil, Tag } from 'lucide-react'

const PAGE_SIZE = 10

const STATUS_STYLES: Record<string, string> = {
  completed: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
  processing: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300',
  failed: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
  pending: 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-400',
}

export default function EssayHistory() {
  const navigate = useNavigate()
  const [data, setData] = useState<any>(null)
  const [page, setPage] = useState(1)
  const [taskType, setTaskType] = useState('')
  const [status, setStatus] = useState('')
  const [labelFilter, setLabelFilter] = useState('')

  useEffect(() => {
    const params: any = { page, page_size: PAGE_SIZE }
    if (taskType) params.task_type = taskType
    if (status) params.status = status
    api.get('/essays', { params }).then(r => setData(r.data))
  }, [page, taskType, status])

  const handleDelete = async (e: React.MouseEvent, essayId: string) => {
    e.stopPropagation()
    if (!confirm('Delete this essay and its scoring history?')) return
    await api.delete(`/essays/${essayId}`)
    setData((prev: any) => prev && { ...prev, items: prev.items.filter((it: any) => it.id !== essayId) })
  }

  const handleEdit = (e: React.MouseEvent, essayId: string) => {
    e.stopPropagation()
    navigate(`/essay/${essayId}/edit`)
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1
  const distinctLabels: string[] = Array.from(new Set((data?.items || []).map((e: any) => e.exam_label).filter(Boolean)))
  const visibleItems = (data?.items || []).filter((e: any) => !labelFilter || e.exam_label === labelFilter)

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Essay History</h1>
        <div className="flex items-center gap-2">
          <select value={taskType} onChange={e => { setTaskType(e.target.value); setPage(1) }} className="px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-sm">
            <option value="">All Tasks</option>
            <option value="task1">Task 1</option>
            <option value="task2">Task 2</option>
          </select>
          <select value={status} onChange={e => { setStatus(e.target.value); setPage(1) }} className="px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-sm">
            <option value="">All Statuses</option>
            <option value="completed">Completed</option>
            <option value="processing">Processing</option>
            <option value="failed">Failed</option>
            <option value="pending">Pending</option>
          </select>
          {distinctLabels.length > 0 && (
            <select value={labelFilter} onChange={e => setLabelFilter(e.target.value)} className="px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-sm">
              <option value="">All Labels</option>
              {distinctLabels.map(l => <option key={l} value={l}>{l}</option>)}
            </select>
          )}
        </div>
      </div>

      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700">
        {visibleItems.length === 0 && (
          <div className="p-8 text-center text-slate-500">
            No essays match these filters.{' '}
            <button onClick={() => navigate('/new-essay')} className="text-blue-600 hover:underline">Write a new essay</button>
          </div>
        )}
        {visibleItems.map((essay: any) => {
          const editable = essay.status === 'pending' || essay.status === 'failed'
          return (
            <div key={essay.id} onClick={() => navigate(`/essay/${essay.id}`)}
              className="px-5 py-3 border-b border-slate-100 dark:border-slate-700 last:border-0 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-750 group">
              <div className="flex items-center justify-between">
                <div>
                  <span className="font-medium">{essay.task_type?.toUpperCase()}</span>
                  <span className="ml-2 text-sm text-slate-500">{essay.word_count} words</span>
                  {essay.essay_type && <span className="ml-2 text-xs text-slate-400 capitalize">{essay.essay_type.replace(/_/g, ' ')}</span>}
                  {essay.created_at && <span className="ml-2 text-xs text-slate-400">{new Date(essay.created_at).toLocaleDateString()}</span>}
                  {essay.exam_label && (
                    <span className="ml-2 inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300">
                      <Tag className="w-3 h-3" /> {essay.exam_label}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_STYLES[essay.status] || STATUS_STYLES.pending}`}>{essay.status}</span>
                  {editable && (
                    <button onClick={e => handleEdit(e, essay.id)} className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-blue-100 dark:hover:bg-blue-900/30 text-blue-500 transition-opacity">
                      <Pencil className="w-4 h-4" />
                    </button>
                  )}
                  <button onClick={e => handleDelete(e, essay.id)} className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-100 dark:hover:bg-red-900/30 text-red-500 transition-opacity">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
              <p className="text-sm text-slate-500 mt-1 truncate">{essay.essay_text.slice(0, 160)}...</p>
            </div>
          )
        })}
      </div>

      {data && data.total > PAGE_SIZE && (
        <div className="flex items-center justify-center gap-3">
          <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1}
            className="flex items-center gap-1 px-3 py-1.5 text-sm border rounded-lg disabled:opacity-40 hover:bg-slate-100 dark:hover:bg-slate-700">
            <ChevronLeft className="w-4 h-4" /> Prev
          </button>
          <span className="text-sm text-slate-500">Page {page} of {totalPages}</span>
          <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page >= totalPages}
            className="flex items-center gap-1 px-3 py-1.5 text-sm border rounded-lg disabled:opacity-40 hover:bg-slate-100 dark:hover:bg-slate-700">
            Next <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  )
}
