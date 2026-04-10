# EcomIntel : AI-Powered Ecommerce Intelligence Platform

A full-stack web application that analyzes ecommerce store URLs and produces enriched intelligence reports for GTM and sales teams.

---

## What It Detects

| Signal | Examples |
|--------|----------|
| **Platform** | Shopify, WooCommerce, BigCommerce, Webflow, Squarespace, Wix, Magento... |
| **Email Marketing** | Klaviyo, Mailchimp, Omnisend, Drip, HubSpot, Brevo, Listrak... |
| **SMS Marketing** | Attentive, Postscript, Klaviyo SMS, SMSBump, Yotpo SMS, Recart... |
| **Lead Capture / Popups** | Privy, Justuno, Klaviyo Forms, OptinMonster, Wheelio, Gorgias... |
| **Analytics Stack** | GA4, GTM, Meta Pixel, TikTok, Pinterest, Hotjar, Segment, Triple Whale... |
| **Review Platforms** | Yotpo, Judge.me, Loox, Stamped.io, Okendo, Trustpilot... |
| **Loyalty Programs** | Smile.io, LoyaltyLion, Marsello, Growave... |
| **Subscriptions** | ReCharge, Skio, Ordergroove, Loop Subscriptions... |
| **Industry / Category** | Inferred from page content and products |
| **Sample Products** | Live product names pulled from Shopify API or schema.org markup |

---

## Architecture

```
frontend/ (React + Vite — Node.js)
  └── calls → backend/ (FastAPI — Python)
                 └── scrapes → ecommerce store URLs
```

**Streaming**: The backend uses Server-Sent Events (SSE). Results stream to the UI as each URL is analyzed, so you see reports appear in real time — no waiting for all 20 to finish.

---

## Tech Stack

### Backend (Python)
- **FastAPI** — async API framework
- **httpx** — async HTTP client with redirect/SSL handling
- **BeautifulSoup4 + lxml** — HTML parsing
- **uvicorn** — ASGI server

### Frontend (Node / React)
- **React 18** — component UI
- **Vite** — build tool and dev server
- **Custom CSS** — no UI library, full design control
- **Fonts**: Oxanium (display) + Outfit (body) + DM Mono (data)

---

## Local Development

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Backend runs at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs`

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: `http://localhost:3000`

The Vite dev server proxies `/api` → `http://localhost:8000`, so no CORS config needed locally.

---

## Environment Variables

### Frontend
Create `frontend/.env.local`:
```
VITE_API_URL=http://localhost:8000
```
For production, set this to your deployed backend URL.

### Backend
Create `backend/.env`:
```
PORT=8000
```

---

## Deployment

### Option A: Railway (Recommended — Free Tier)

1. Push to a GitHub repo
2. Create two Railway services — one for backend, one for frontend
3. **Backend service**:
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Root: `backend/`
4. **Frontend service**:
   - Build command: `npm install && npm run build`
   - Start command: `npx serve dist --port $PORT`
   - Root: `frontend/`
   - Env var: `VITE_API_URL=<your backend railway URL>`

### Option B: Render (Free Tier)

1. Create a Web Service for the backend (Python)
2. Create a Static Site for the frontend (Node build)
3. Set `VITE_API_URL` env var on the frontend static site

### Option C: Vercel (Frontend) + Render (Backend)

1. Deploy backend to Render as a Python service
2. Deploy frontend to Vercel
3. Add `VITE_API_URL=<render backend URL>` to Vercel env vars

---

## API Reference

### `POST /analyze`
Streams results as SSE.

**Request:**
```json
{
  "urls": ["https://example.com", "https://store2.com"]
}
```

**SSE Events:**
```
data: {"type": "meta", "total": 2}
data: {"type": "result", "index": 0, "url": "...", "platform": "Shopify", ...}
data: {"type": "result", "index": 1, "url": "...", "status": "timeout", ...}
data: {"type": "done"}
```

### `GET /health`
Returns `{"status": "ok"}`.

---

## Design Decisions

- **Sequential processing** (not parallel) to be respectful of rate limits and avoid IP blocks. 0.3s delay between requests.
- **Graceful error handling**: timeout, HTTP errors, and parsing failures all produce structured error objects — never silent failures.
- **SSE streaming** over WebSockets: simpler to deploy, works with standard HTTP infrastructure.
- **lxml parser** over html.parser: faster and more lenient with broken HTML.
- **SSL verification disabled** (`verify=False`): many DTC stores have CDN configs that cause SSL issues; this is acceptable for public scraping.
- **Favicon via Google S2 API**: `https://www.google.com/s2/favicons?domain=...&sz=64` — free, reliable, no API key.
- **Shopify product endpoint** (`/products.json`): publicly accessible on most Shopify stores, returns structured product data without authentication.
- **Industry detection** uses weighted keyword scoring across title, meta description, and product names.

---

## Limitations

- JavaScript-rendered content is not analyzed (no headless browser). Scripts loaded client-side after page load won't be in the HTML source.
- Some tools inject via GTM and won't appear in initial HTML.
- Sites behind Cloudflare Bot Protection may return 403s.
- Shopify `/products.json` endpoint can be disabled by store owners.

---

## Future Enhancements

- [ ] Puppeteer/Playwright integration for JS rendering
- [ ] Export to CSV/Excel
- [ ] CRM push (HubSpot / Salesforce)
- [ ] Batch job queue with Redis
- [ ] Caching layer (Redis) to avoid re-scraping
- [ ] Estimated revenue signals (Alexa rank, SimilarWeb)
- [ ] Historical diff — track tech stack changes over time
