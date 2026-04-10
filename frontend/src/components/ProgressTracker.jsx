import { useEffect, useRef } from 'react'

export default function ProgressTracker({ total, completed, logs, results }) {
  const logRef = useRef(null)

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight
    }
  }, [logs])

  const pct = total > 0 ? Math.round((completed / total) * 100) : 0
  const successCount = results.filter(r => r.status === 'success').length
  const errorCount = results.filter(r => r.status !== 'success').length

  return (
    <div className="progress-wrapper">
      <div className="progress-header">
        <div className="progress-title">
          {completed < total ? (
            <>
              <span className="scanning-ring" />
              Scanning Stores
            </>
          ) : (
            <>
              <span style={{ color: 'var(--green)' }}>✓</span>
              Analysis Complete
            </>
          )}
        </div>
        <div className="progress-stats mono">
          <span className="text-cyan">{completed}</span>
          <span style={{ color: 'var(--text-4)' }}> / {total}</span>
          <span style={{ color: 'var(--text-4)', marginLeft: '8px' }}>{pct}%</span>
        </div>
      </div>

      <div className="progress-bar-wrap">
        <div
          className="progress-bar-fill"
          style={{ width: `${pct}%` }}
        />
      </div>

      {completed === total && total > 0 && (
        <div style={{
          display: 'flex', gap: '16px', flexWrap: 'wrap',
          padding: '10px 16px',
          background: 'var(--bg-panel)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-sm)',
        }}>
          <span style={{ fontSize: '12px', color: 'var(--text-2)' }}>
            <span className="text-green mono">{successCount}</span> successful
          </span>
          {errorCount > 0 && (
            <span style={{ fontSize: '12px', color: 'var(--text-2)' }}>
              <span className="text-red mono">{errorCount}</span> failed
            </span>
          )}
          <span style={{ fontSize: '12px', color: 'var(--text-4)', marginLeft: 'auto' }}>
            Scroll down to view reports ↓
          </span>
        </div>
      )}

      <div className="progress-log" ref={logRef}>
        {logs.map((log, i) => (
          <div key={i} className={`log-line ${log.state}`}>
            <div className={`log-status ${log.state}`}>
              {log.state === 'done' && '✓'}
              {log.state === 'error' && '✕'}
            </div>
            <span style={{ color: 'var(--text-4)' }}>
              [{String(log.index + 1).padStart(2, '0')}]
            </span>
            <span>{log.domain}</span>
            {log.platform && log.state === 'done' && (
              <span style={{ color: 'var(--text-4)', marginLeft: 'auto', fontSize: '10px' }}>
                {log.platform}
              </span>
            )}
            {log.elapsed && (
              <span style={{ color: 'var(--text-4)', marginLeft: 'auto', fontSize: '10px' }}>
                {log.elapsed}ms
              </span>
            )}
          </div>
        ))}
        {completed < total && (
          <div className="log-line active">
            <div className="log-status active" />
            <span>Scanning next target...</span>
          </div>
        )}
      </div>
    </div>
  )
}
