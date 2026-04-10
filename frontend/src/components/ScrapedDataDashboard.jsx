import { Fragment } from 'react'

/**
 * Per-URL dashboard: every key returned by the analyze API / scraper,
 * independent of the categorized intelligence report.
 */

const SKIP_KEYS = new Set(['type', 'index'])

function humanizeKey(key) {
  if (!key) return ''
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase())
}

function formatValue(value) {
  if (value === null || value === undefined || value === '') {
    return { kind: 'empty', text: '—' }
  }
  if (Array.isArray(value)) {
    return { kind: 'list', items: value }
  }
  if (typeof value === 'object') {
    return { kind: 'json', text: JSON.stringify(value, null, 2) }
  }
  return { kind: 'text', text: String(value) }
}

/** Stable order: identity → status → commerce → tool buckets → meta → rest alpha */
const KEY_ORDER = [
  'url',
  'normalized_url',
  'domain',
  'store_name',
  'favicon',
  'status',
  'error',
  'platform',
  'description',
  'industry',
  'sample_products',
  'email_marketing',
  'sms_marketing',
  'popup_tools',
  'analytics',
  'review_tools',
  'loyalty_tools',
  'subscription_tools',
  'tech_count',
  'elapsed_ms',
  'render_source',
  'apify_html_chars',
]

function sortedEntries(obj) {
  const keys = Object.keys(obj).filter(k => !SKIP_KEYS.has(k))
  const rank = new Map(KEY_ORDER.map((k, i) => [k, i]))
  return keys.sort((a, b) => {
    const ra = rank.has(a) ? rank.get(a) : 1000
    const rb = rank.has(b) ? rank.get(b) : 1000
    if (ra !== rb) return ra - rb
    return a.localeCompare(b)
  })
}

function KeyPointPair({ rawKey, formatted }) {
  const label = humanizeKey(rawKey)
  return (
    <Fragment>
      <dt className="key-point-label">{label}</dt>
      <dd className="key-point-value">
        {formatted.kind === 'empty' && (
          <span className="key-point-empty">{formatted.text}</span>
        )}
        {formatted.kind === 'text' && (
          <span className="mono">{formatted.text}</span>
        )}
        {formatted.kind === 'list' && (
          formatted.items.length === 0 ? (
            <span className="key-point-empty">—</span>
          ) : (
            <ul className="key-point-list">
              {formatted.items.map((item, i) => (
                <li key={`${rawKey}-${i}`}>{String(item)}</li>
              ))}
            </ul>
          )
        )}
        {formatted.kind === 'json' && (
          <pre className="key-point-json">{formatted.text}</pre>
        )}
      </dd>
    </Fragment>
  )
}

export default function ScrapedDataDashboard({ results }) {
  if (!results || results.length === 0) return null

  return (
    <div className="scraped-dashboard">
      <div className="scraped-dashboard-header">
        <div className="scraped-dashboard-title">Scraped data — full API payload</div>
        <div className="scraped-dashboard-sub">
          Every field returned for each URL (raw scraper / API output), separate from the intelligence report above.
        </div>
      </div>

      <div className="scraped-panels">
        {results.map((result, i) => {
          const title =
            result.store_name ||
            result.domain ||
            result.url ||
            `URL ${i + 1}`
          const keys = sortedEntries(result)

          return (
            <article
              key={`${result.url}-${i}`}
              className="scraped-panel"
              style={{ animationDelay: `${i * 40}ms` }}
            >
              <header className="scraped-panel-header">
                <span className="scraped-panel-title">{title}</span>
                <a
                  className="scraped-panel-link mono"
                  href={result.normalized_url || result.url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {result.normalized_url || result.url}
                </a>
              </header>
              <dl className="key-points-grid">
                {keys.map(k => (
                  <KeyPointPair
                    key={k}
                    rawKey={k}
                    formatted={formatValue(result[k])}
                  />
                ))}
              </dl>
            </article>
          )
        })}
      </div>
    </div>
  )
}
