import { useState, useRef, useEffect } from 'react'
import URLInput from './components/URLInput'
import ProgressTracker from './components/ProgressTracker'
import ReportDashboard from './components/ReportDashboard'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

function extractDomain(url) {
  try {
    return new URL(url.startsWith('http') ? url : 'https://' + url).hostname.replace('www.', '')
  } catch {
    return url
  }
}

export default function App() {
  const [phase, setPhase] = useState('idle') // idle | analyzing | done
  const [results, setResults] = useState([])
  const [logs, setLogs] = useState([])
  const [total, setTotal] = useState(0)
  const [completed, setCompleted] = useState(0)
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('theme')
    if (saved === 'light' || saved === 'dark') return saved
    return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark'
  })
  const abortRef = useRef(null)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }, [theme])

  async function handleAnalyze(urls) {
    setPhase('analyzing')
    setResults([])
    setLogs([])
    setTotal(urls.length)
    setCompleted(0)

    const controller = new AbortController()
    abortRef.current = controller

    try {
      const response = await fetch(`${API_BASE}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ urls }),
        signal: controller.signal,
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() // keep incomplete line

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const data = JSON.parse(line.slice(6))

            if (data.type === 'meta') {
              setTotal(data.total)

            } else if (data.type === 'result') {
              const domain = extractDomain(data.url)
              setCompleted(prev => prev + 1)
              setResults(prev => [...prev, data])
              setLogs(prev => [...prev, {
                index: data.index,
                domain,
                state: data.status === 'success' ? 'done' : 'error',
                platform: data.platform,
                elapsed: data.elapsed_ms,
              }])

            } else if (data.type === 'done') {
              setPhase('done')
            }
          } catch {
            // skip malformed SSE line
          }
        }
      }

      setPhase('done')

    } catch (err) {
      if (err.name !== 'AbortError') {
        console.error('Analysis error:', err)
        setPhase('done')
      } else {
        setPhase('done')
      }
    }
  }

  function handleStop() {
    abortRef.current?.abort()
    setPhase('done')
  }

  function handleReset() {
    setPhase('idle')
    setResults([])
    setLogs([])
    setTotal(0)
    setCompleted(0)
  }

  function toggleTheme() {
    setTheme(prev => (prev === 'dark' ? 'light' : 'dark'))
  }

  return (
    <div className="app-layout">
      {/* Top bar */}
      <header className="topbar">
        <div className="brand">
          <span className="brand-name">Ecom<span>Intel</span></span>
        </div>
        <div className="topbar-meta">
          <div className="status-dot">API LIVE</div>
          <button className="theme-toggle-btn" onClick={toggleTheme}>
            {theme === 'dark' ? 'Light mode' : 'Dark mode'}
          </button>
          {results.length > 0 && (
            <button
              onClick={handleReset}
              style={{
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border)',
                color: 'var(--text-2)',
                padding: '5px 12px',
                borderRadius: 'var(--radius-sm)',
                fontSize: '12px',
                cursor: 'pointer',
                fontFamily: 'var(--font-body)',
              }}
            >
              New Analysis
            </button>
          )}
        </div>
      </header>

      {/* Main layout */}
      <div className="main-content">
        <URLInput
          onAnalyze={handleAnalyze}
          isAnalyzing={phase === 'analyzing'}
          onStop={handleStop}
        />

        <main className="results-area">
          {phase === 'idle' && results.length === 0 && <EmptyState />}

          {(phase === 'analyzing' || results.length > 0) && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
              {phase === 'analyzing' && (
                <ProgressTracker
                  total={total}
                  completed={completed}
                  logs={logs}
                  results={results}
                />
              )}

              {results.length > 0 && (
                <div>
                  <div className="results-header">
                    <div className="results-title">
                      Intelligence Reports
                    </div>
                    <div className="results-count mono">
                      {results.length} store{results.length !== 1 ? 's' : ''}
                    </div>
                  </div>
                  <ReportDashboard results={results} />
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  )
}

function EmptyState() {
  return (
    <div className="empty-state">
      <div className="empty-icon">🔍</div>
      <div className="empty-title">Ready to Scan</div>
      <div className="empty-sub">
        Enter ecommerce store URLs in the sidebar and run analysis to get deep intelligence reports on each store's tech stack.
      </div>
      <div className="feature-list">
        {[
          { label: 'Platform Detection', color: '#95bf47' },
          { label: 'Email & SMS Tools', color: '#67e8f9' },
          { label: 'Lead Capture', color: '#fcd34d' },
          { label: 'Analytics Stack', color: '#93c5fd' },
          { label: 'Review Platforms', color: '#f9a8d4' },
          { label: 'Sample Products', color: '#c4b5fd' },
        ].map(f => (
          <div key={f.label} className="feature-item">
            <span className="dot" style={{ background: f.color }} />
            {f.label}
          </div>
        ))}
      </div>
    </div>
  )
}
