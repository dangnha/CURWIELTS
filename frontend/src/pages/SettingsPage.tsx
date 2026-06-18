import { useState, useEffect } from 'react'
import api from '../lib/api'
import { Save, RefreshCw, CheckCircle2, Search, Wifi, XCircle } from 'lucide-react'

const PROVIDERS = [
  { value: 'gemini', label: 'Gemini (Google)' },
  { value: 'chatgpt', label: 'ChatGPT (OpenAI)' },
  { value: 'deepseek', label: 'DeepSeek' },
  { value: 'grok', label: 'Grok (xAI)' },
  { value: 'groq', label: 'Groq (GroqCloud)' },
]

export default function SettingsPage() {
  const [provider, setProvider] = useState('gemini')
  const [apiKey, setApiKey] = useState('')
  const [model, setModel] = useState('')
  const [temperature, setTemperature] = useState(0.3)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  // Model fetching
  const [availableModels, setAvailableModels] = useState<{ name: string; display_name?: string; description?: string }[]>([])
  const [fetchingModels, setFetchingModels] = useState(false)
  const [modelFetchError, setModelFetchError] = useState('')
  const [showModelDropdown, setShowModelDropdown] = useState(false)

  const [kbStatus, setKbStatus] = useState<any>(null)
  const [ingesting, setIngesting] = useState(false)

  // Connection test
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<{ ok: boolean; error?: string; latency_ms?: number } | null>(null)

  useEffect(() => {
    api.get('/admin/settings').then(r => {
      if (r.data?.llm_config) {
        const c = r.data.llm_config
        if (c.provider) setProvider(c.provider)
        if (c.api_key) setApiKey(c.api_key)
        if (c.model) setModel(c.model)
        if (c.temperature != null) setTemperature(c.temperature)
      }
    })
    api.get('/admin/kb/status').then(r => setKbStatus(r.data))
  }, [])

  const fetchModels = async () => {
    if (!apiKey.trim()) return
    setFetchingModels(true)
    setModelFetchError('')
    try {
      const res = await api.post('/models/fetch-models', { provider, api_key: apiKey })
      if (res.data.models?.length > 0) {
        const flat = res.data.models.map((m: any) => typeof m === 'string' ? { name: m } : m)
        setAvailableModels(flat)
        setShowModelDropdown(true)
        if (!model && flat[0]) setModel(flat[0].name)
      }
      if (res.data.error) setModelFetchError(res.data.error)
    } catch (e: any) {
      setModelFetchError(e.response?.data?.detail || 'Failed to fetch models')
    }
    setFetchingModels(false)
  }

  const handleTestConnection = async () => {
    if (!apiKey.trim()) return
    setTesting(true)
    setTestResult(null)
    try {
      const res = await api.post('/admin/test-connection', { provider, api_key: apiKey, model: model.trim() || undefined, temperature })
      setTestResult(res.data)
    } catch (e: any) {
      setTestResult({ ok: false, error: e.response?.data?.detail || 'Test failed' })
    }
    setTesting(false)
  }

  const handleSave = async () => {
    if (!model.trim()) {
      alert('Please enter or select a model name')
      return
    }
    setSaving(true)
    try {
      await api.put('/admin/settings', { provider, api_key: apiKey, model: model.trim(), temperature })
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (e: any) { alert('Save failed') }
    setSaving(false)
  }

  const handleIngest = async () => {
    setIngesting(true)
    try {
      const res = await api.post('/admin/kb/ingest')
      setKbStatus(res.data)
    } catch {}
    setIngesting(false)
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>

      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
        <h2 className="font-semibold text-lg mb-4">LLM Provider Configuration</h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
          Configure your AI provider. The selected provider and model will be used by <strong>all scoring agents</strong>.
        </p>

        <div className="space-y-4">
          {/* Provider */}
          <div>
            <label className="block text-sm font-medium mb-1 text-slate-700 dark:text-slate-300">Provider</label>
            <select
              value={provider}
              onChange={e => { setProvider(e.target.value); setModel(''); setAvailableModels([]); setShowModelDropdown(false) }}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-sm"
            >
              {PROVIDERS.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
            </select>
          </div>

          {/* API Key */}
          <div>
            <label className="block text-sm font-medium mb-1 text-slate-700 dark:text-slate-300">API Key</label>
            <input
              type="password"
              value={apiKey}
              onChange={e => setApiKey(e.target.value)}
              placeholder="Paste your API key..."
              className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-sm font-mono"
            />
            <p className="text-xs text-slate-400 mt-1">Your API key is stored locally and never shared.</p>
          </div>

          {/* Model */}
          <div>
            <label className="block text-sm font-medium mb-1 text-slate-700 dark:text-slate-300">Model</label>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <input
                  type="text"
                  value={model}
                  onChange={e => { setModel(e.target.value); setShowModelDropdown(false) }}
                  onFocus={() => availableModels.length > 0 && setShowModelDropdown(true)}
                  placeholder="e.g., gemini-2.0-flash, gemini-2.5-pro..."
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-sm font-mono"
                />
                {showModelDropdown && availableModels.length > 0 && (
                  <div className="absolute z-10 top-full mt-1 w-full bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                    {availableModels.map(m => (
                      <button
                        key={m.name}
                        onClick={() => { setModel(m.name); setShowModelDropdown(false) }}
                        className="w-full text-left px-3 py-2 text-sm hover:bg-blue-50 dark:hover:bg-blue-900/30 border-b border-slate-100 dark:border-slate-600 last:border-0"
                      >
                        <div className="font-medium font-mono">{m.name}</div>
                        {m.display_name && <div className="text-xs text-slate-500">{m.display_name}</div>}
                        {m.description && <div className="text-xs text-slate-400">{m.description}</div>}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              <button
                onClick={fetchModels}
                disabled={fetchingModels || !apiKey.trim()}
                className="flex items-center gap-1 px-3 py-2 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 disabled:opacity-50 rounded-lg text-sm font-medium"
                title="Fetch available models from your API key"
              >
                {fetchingModels ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                Fetch
              </button>
            </div>
            {modelFetchError && <p className="text-xs text-amber-600 mt-1">{modelFetchError}</p>}
            <p className="text-xs text-slate-400 mt-1">
              Type any model name or click <strong>Fetch</strong> to list models available for your API key.
            </p>
          </div>

          {/* Temperature */}
          <div>
            <label className="block text-sm font-medium mb-1 text-slate-700 dark:text-slate-300">Temperature: {temperature}</label>
            <input type="range" min={0} max={1} step={0.1} value={temperature} onChange={e => setTemperature(parseFloat(e.target.value))} className="w-full" />
            <div className="flex justify-between text-xs text-slate-400"><span>0 (Deterministic)</span><span>1 (Creative)</span></div>
          </div>

          <div className="flex items-center gap-3 flex-wrap">
            <button
              onClick={handleSave}
              disabled={saving || !apiKey || !model.trim()}
              className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg font-medium"
            >
              {saved ? <><CheckCircle2 className="w-4 h-4" /> Saved</> : saving ? <><RefreshCw className="w-4 h-4 animate-spin" /> Saving...</> : <><Save className="w-4 h-4" /> Save Configuration</>}
            </button>
            <button
              onClick={handleTestConnection}
              disabled={testing || !apiKey.trim()}
              className="flex items-center gap-2 px-4 py-2.5 border border-slate-300 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-700 disabled:opacity-50 rounded-lg font-medium text-sm"
            >
              {testing ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Wifi className="w-4 h-4" />} Test Connection
            </button>
            {testResult && (
              testResult.ok ? (
                <span className="flex items-center gap-1 text-sm text-green-600"><CheckCircle2 className="w-4 h-4" /> Connected ({testResult.latency_ms}ms)</span>
              ) : (
                <span className="flex items-center gap-1 text-sm text-red-600"><XCircle className="w-4 h-4" /> {testResult.error}</span>
              )
            )}
          </div>
        </div>
      </div>

      {/* Knowledge Base */}
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
        <h2 className="font-semibold text-lg mb-3">Knowledge Base</h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">The knowledge base contains Vietnamese IELTS reference materials used by agents for better scoring.</p>
        <div className="flex items-center justify-between">
          <div>
            <span className="text-sm">Status: <span className={kbStatus?.status === 'ready' ? 'text-green-600 font-medium' : 'text-red-500'}>{kbStatus?.status || 'Unknown'}</span></span>
            {kbStatus?.document_count != null && <span className="text-sm text-slate-500 ml-2">({kbStatus.document_count} chunks)</span>}
          </div>
          <button onClick={handleIngest} disabled={ingesting} className="px-4 py-2 bg-slate-600 hover:bg-slate-700 disabled:opacity-50 text-white rounded-lg text-sm">
            {ingesting ? <RefreshCw className="w-4 h-4 animate-spin inline" /> : 'Re-Ingest KB'}
          </button>
        </div>
      </div>
    </div>
  )
}
