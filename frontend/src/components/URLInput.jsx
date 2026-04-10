import { useState, useEffect } from 'react'

const PRESET_URLS = `https://www.allbirds.com
https://www.gymshark.com
https://www.brooklinen.com
https://www.beardbrand.com
https://www.puravidabracelets.com
https://www.chubbiesshorts.com
https://www.shinesty.com
https://www.kettleandfire.com
https://www.mudwtr.com
https://www.graza.co
https://www.olipop.com
https://www.jonesroadbeauty.com
https://www.halfdays.com
https://www.goodr.com
https://www.bombas.com
https://www.ruggable.com
https://www.studs.com
https://www.fishwifetinnedfishco.com
https://www.hexclad.com
https://www.skullcandy.com`

function countUrls(text) {
  return text.split('\n').filter(l => l.trim().length > 0).length
}

export default function URLInput({ onAnalyze, isAnalyzing, onStop }) {
  const [text, setText] = useState('')
  const urlCount = countUrls(text)

  function handleAnalyze() {
    const urls = text.split('\n').map(l => l.trim()).filter(Boolean)
    if (urls.length > 0) onAnalyze(urls)
  }

  function loadPreset() {
    setText(PRESET_URLS)
  }

  function clearAll() {
    setText('')
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2>Intelligence Scanner</h2>
        <p>Enter ecommerce URLs to analyze their tech stack, tools, products, and industry.</p>
      </div>

      <div className="url-input-wrapper">
        <div className="url-textarea-label">
          Target URLs
          {urlCount > 0 && (
            <span className="count-badge">{urlCount}</span>
          )}
        </div>

        <textarea
          className="url-textarea"
          value={text}
          onChange={e => setText(e.target.value)}
          placeholder={"https://example.com\nhttps://another-store.com\n..."}
          disabled={isAnalyzing}
          spellCheck={false}
        />

        <div className="url-textarea-actions">
          <button className="btn-ghost" onClick={loadPreset} disabled={isAnalyzing}>
            Load Demo
          </button>
          <button className="btn-ghost" onClick={clearAll} disabled={isAnalyzing}>
            Clear
          </button>
        </div>

        {!isAnalyzing ? (
          <button
            className="btn-primary"
            onClick={handleAnalyze}
            disabled={urlCount === 0}
          >
            <span>⚡</span>
            Run Analysis
            {urlCount > 0 && <span style={{ opacity: 0.7, fontSize: '12px' }}>({urlCount})</span>}
          </button>
        ) : (
          <button className="btn-danger" onClick={onStop}>
            <span>◼</span>
            Stop Analysis
          </button>
        )}
      </div>

      <div className="preset-section">
        <div className="preset-label">Quick Load</div>
        <button className="preset-btn" onClick={loadPreset}>
          <span>Assessment URLs (20 stores)</span>
          <span className="text-cyan">→</span>
        </button>
      </div>

      <div style={{ marginTop: 'auto', paddingTop: '16px', borderTop: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {[
            { label: 'Platform Detection', color: '#95bf47' },
            { label: 'Email Marketing', color: '#67e8f9' },
            { label: 'SMS Providers', color: '#6ee7b7' },
            { label: 'Lead Capture Tools', color: '#fcd34d' },
            { label: 'Analytics Stack', color: '#93c5fd' },
            { label: 'Reviews & Loyalty', color: '#f9a8d4' },
            { label: 'Subscription Tools', color: '#fdba74' },
            { label: 'Sample Products', color: '#c4b5fd' },
          ].map(f => (
            <div key={f.label} style={{
              display: 'flex', alignItems: 'center', gap: '8px',
              fontSize: '12px', color: 'var(--text-3)'
            }}>
              <span style={{
                width: '6px', height: '6px', borderRadius: '50%',
                background: f.color, flexShrink: 0,
                boxShadow: `0 0 6px ${f.color}60`
              }} />
              {f.label}
            </div>
          ))}
        </div>
      </div>
    </aside>
  )
}
