import { useState } from 'react'

function platformClass(platform) {
  if (!platform) return 'platform-default'
  const p = platform.toLowerCase()
  if (p.includes('shopify')) return 'platform-shopify'
  if (p.includes('woocommerce')) return 'platform-woocommerce'
  if (p.includes('bigcommerce')) return 'platform-bigcommerce'
  if (p.includes('squarespace')) return 'platform-squarespace'
  if (p.includes('webflow')) return 'platform-webflow'
  if (p.includes('wix')) return 'platform-wix'
  if (p.includes('magento')) return 'platform-magento'
  return 'platform-default'
}

function ChipRow({ items, chipClass, emptyText }) {
  if (!items || items.length === 0) {
    return (
      <div className="chips-row">
        <span className="chip chip-none">{emptyText || 'None detected'}</span>
      </div>
    )
  }
  return (
    <div className="chips-row">
      {items.map(item => (
        <span key={item} className={`chip ${chipClass}`}>{item}</span>
      ))}
    </div>
  )
}

function Section({ label, children, fullWidth }) {
  return (
    <div className={`card-section${fullWidth ? ' full-width' : ''}`}>
      <div className="section-label">{label}</div>
      {children}
    </div>
  )
}

export default function StoreCard({ result, index }) {
  const [expanded, setExpanded] = useState(true)

  const {
    store_name, url, normalized_url, domain, status, favicon,
    platform, description, industry, sample_products,
    email_marketing, sms_marketing, popup_tools, analytics,
    review_tools, loyalty_tools, subscription_tools,
    tech_count, error, elapsed_ms
  } = result

  const isError = status !== 'success'

  return (
    <div
      className={`store-card status-${status}`}
      style={{ animationDelay: `${index * 60}ms` }}
    >
      {/* Header */}
      <div className="card-header" onClick={() => setExpanded(e => !e)}>
        <div className="card-favicon">
          {favicon ? (
            <img
              src={favicon}
              alt=""
              onError={e => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex'; }}
            />
          ) : null}
          <span style={{ display: favicon ? 'none' : 'flex', fontSize: '16px' }}>🏪</span>
        </div>

        <div className="card-title-group">
          <div className="card-store-name">{store_name || domain}</div>
          <div className="card-url">
            <a href={normalized_url || url} target="_blank" rel="noopener noreferrer"
               onClick={e => e.stopPropagation()}>
              {domain || url}
            </a>
          </div>
        </div>

        <div className="card-header-right">
          {platform && (
            <span className={`platform-badge ${platformClass(platform)}`}>
              {platform}
            </span>
          )}
          <span className={`status-badge status-${status}`}>
            {status === 'success' ? '● OK' : status === 'timeout' ? '◐ TIMEOUT' : '● ERR'}
          </span>
          <span className={`expand-toggle ${expanded ? 'open' : ''}`}>▼</span>
        </div>
      </div>

      {/* Body */}
      {expanded && (
        <div className="card-body">

          {/* Quick info row */}
          <div className="card-quick-info">
            {industry && (
              <span className="industry-tag">
                🏷️ {industry}
              </span>
            )}
            {!isError && (
              <span className="tech-total-tag">
                ⚡ {tech_count} tools detected
              </span>
            )}
            {elapsed_ms > 0 && (
              <span className="elapsed-tag">{elapsed_ms}ms</span>
            )}
          </div>

          {/* Description */}
          {description && (
            <div className="card-description">"{description}"</div>
          )}

          {/* Error state */}
          {isError && (
            <div className="error-body">
              <span className="error-icon">⚠</span>
              <div>
                <div style={{ fontWeight: 600, marginBottom: '4px' }}>
                  {status === 'timeout' ? 'Request Timed Out' : 'Analysis Failed'}
                </div>
                <div style={{ fontSize: '12px', opacity: 0.8 }}>{error}</div>
              </div>
            </div>
          )}

          {/* Tech sections */}
          {!isError && (
            <div className="card-sections">

              <Section label="Email Marketing">
                <ChipRow items={email_marketing} chipClass="chip-email" emptyText="None detected" />
              </Section>

              <Section label="SMS Marketing">
                <ChipRow items={sms_marketing} chipClass="chip-sms" emptyText="None detected" />
              </Section>

              <Section label="Popup / Lead Capture">
                <ChipRow items={popup_tools} chipClass="chip-popup" emptyText="None detected" />
              </Section>

              <Section label="Analytics Stack">
                <ChipRow items={analytics} chipClass="chip-analytics" emptyText="None detected" />
              </Section>

              <Section label="Reviews">
                <ChipRow items={review_tools} chipClass="chip-review" emptyText="None detected" />
              </Section>

              <Section label="Loyalty & Subscriptions">
                <ChipRow
                  items={[...(loyalty_tools || []), ...(subscription_tools || [])]}
                  chipClass="chip-loyalty"
                  emptyText="None detected"
                />
              </Section>

              {/* Products - full width */}
              {sample_products && sample_products.length > 0 && (
                <Section label="Sample Products" fullWidth>
                  <div className="products-list">
                    {sample_products.map((p, i) => (
                      <div key={i} className="product-item">{p}</div>
                    ))}
                  </div>
                </Section>
              )}

            </div>
          )}

        </div>
      )}
    </div>
  )
}
