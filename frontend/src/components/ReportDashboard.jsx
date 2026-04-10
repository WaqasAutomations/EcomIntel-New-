import StoreCard from './StoreCard'

function SummaryStat({ value, label, color }) {
  return (
    <div className="summary-stat">
      <div className="summary-stat-value" style={color ? { color } : {}}>
        {value}
      </div>
      <div className="summary-stat-label">{label}</div>
    </div>
  )
}

export default function ReportDashboard({ results }) {
  if (results.length === 0) return null

  const success = results.filter(r => r.status === 'success')
  const shopify = success.filter(r => r.platform === 'Shopify').length
  const avgTools = success.length > 0
    ? Math.round(success.reduce((a, r) => a + (r.tech_count || 0), 0) / success.length)
    : 0
  const hasEmail = success.filter(r => r.email_marketing?.length > 0).length
  const hasSms = success.filter(r => r.sms_marketing?.length > 0).length

  // Platform breakdown
  const platformCounts = {}
  success.forEach(r => {
    const p = r.platform || 'Unknown'
    platformCounts[p] = (platformCounts[p] || 0) + 1
  })

  return (
    <div>
      {/* Summary bar */}
      <div className="results-summary-bar">
        <SummaryStat value={results.length} label="stores analyzed" />
        <div className="summary-divider" />
        <SummaryStat value={success.length} label="successful" color="var(--green)" />
        <div className="summary-divider" />
        <SummaryStat value={shopify} label="on Shopify" color="#95bf47" />
        <div className="summary-divider" />
        <SummaryStat value={hasEmail} label="email tools" color="var(--cyan)" />
        <div className="summary-divider" />
        <SummaryStat value={hasSms} label="sms tools" color="var(--green)" />
        <div className="summary-divider" />
        <SummaryStat value={avgTools} label="avg tools/store" color="var(--accent)" />
      </div>

      {/* Individual cards */}
      <div className="cards-grid">
        {results.map((result, i) => (
          <StoreCard key={result.url + i} result={result} index={i} />
        ))}
      </div>

    </div>
  )
}
