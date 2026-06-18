import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { PenLine, BarChart3, BookOpen, TrendingUp, Settings, Moon, Sun, Menu, History } from 'lucide-react'

type Theme = 'light' | 'dark'

const navItems = [
  { to: '/', icon: BarChart3, label: 'Dashboard' },
  { to: '/new-essay', icon: PenLine, label: 'New Essay' },
  { to: '/essays', icon: History, label: 'History' },
  { to: '/vocabulary', icon: BookOpen, label: 'Vocabulary' },
  { to: '/progress', icon: TrendingUp, label: 'Progress' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

export default function AppShell({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('theme')
      if (stored === 'dark') return 'dark'
    }
    return 'light'
  })
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()

  const toggleTheme = () => {
    const next = theme === 'light' ? 'dark' : 'light'
    setTheme(next)
    localStorage.setItem('theme', next)
    document.documentElement.classList.toggle('dark', next === 'dark')
  }

  return (
    <div className="flex h-screen">
      <aside className={`fixed inset-y-0 left-0 z-40 w-64 bg-white dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700 transform transition-transform ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} md:translate-x-0 md:static`}>
        <div className="flex items-center gap-2 px-6 py-5 border-b border-slate-200 dark:border-slate-700">
          <PenLine className="w-6 h-6 text-blue-600" />
          <span className="font-bold text-lg">IELTS Scorer</span>
        </div>
        <nav className="px-3 py-4 space-y-1">
          {navItems.map((item) => {
            const active = location.pathname === item.to || (item.to !== '/' && location.pathname.startsWith(item.to))
            return (
              <Link
                key={item.to}
                to={item.to}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${active ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300' : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700'}`}
                onClick={() => setSidebarOpen(false)}
              >
                <item.icon className="w-5 h-5" />
                {item.label}
              </Link>
            )
          })}
        </nav>
      </aside>

      {sidebarOpen && <div className="fixed inset-0 z-30 bg-black/30 md:hidden" onClick={() => setSidebarOpen(false)} />}

      <div className="flex-1 flex flex-col min-w-0">
        <header className="flex items-center justify-between px-4 md:px-6 py-3 border-b border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
          <button className="md:hidden p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700" onClick={() => setSidebarOpen(true)}>
            <Menu className="w-5 h-5" />
          </button>
          <div className="flex-1" />
          <button onClick={toggleTheme} className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700">
            {theme === 'light' ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
          </button>
        </header>
        <main className="flex-1 overflow-auto p-4 md:p-6 bg-slate-50 dark:bg-slate-900">
          {children}
        </main>
      </div>
    </div>
  )
}
