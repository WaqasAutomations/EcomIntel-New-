import json
import asyncio
import logging
import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, HttpUrl, validator

# Always load backend/.env regardless of process cwd (e.g. uvicorn from repo root).
load_dotenv(Path(__file__).resolve().parent / ".env")

from scraper import analyze_url, normalize_url
import apify_fetcher

logger = logging.getLogger(__name__)

# Ensure our modules log at INFO when uvicorn runs with default settings.
for _log_name in ("apify_fetcher", "main", "scraper"):
    logging.getLogger(_log_name).setLevel(logging.INFO)

app = FastAPI(
    title="Ecommerce Intelligence API",
    description="Analyzes ecommerce stores for tech stack, tools, and products.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_URLS = 50
# Temporary runtime switch: keep Apify code in repo but use direct scraper path.
USE_APIFY = False


@app.get("/", response_class=HTMLResponse)
async def root():
    """
    Browser-friendly landing page. This server is the JSON API only;
    the React UI runs separately (e.g. Vite on port 57955).
    """
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Ecommerce Intel API</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 42rem; margin: 2rem auto; padding: 0 1rem; line-height: 1.5; }
    h1 { font-size: 1.25rem; }
    a { color: #2563eb; }
    code { background: #f1f5f9; padding: 0.1em 0.35em; border-radius: 4px; }
    ul { padding-left: 1.25rem; }
  </style>
</head>
<body>
  <h1>Ecommerce Intelligence API</h1>
  <p>This address is the <strong>backend API</strong>, not the web app UI. Open the frontend dev server in your browser instead (usually <code>http://127.0.0.1:57955</code> after <code>npm run dev</code> in <code>frontend/</code>).</p>
  <p>Useful links on this server:</p>
  <ul>
    <li><a href="/docs">Interactive API docs (Swagger)</a></li>
    <li><a href="/health"><code>/health</code></a> — API alive</li>
    <li><a href="/health/apify"><code>/health/apify</code></a> — Apify token check</li>
  </ul>
</body>
</html>
"""


class AnalyzeRequest(BaseModel):
    urls: List[str]

    @validator("urls")
    def validate_urls(cls, v):
        if not v:
            raise ValueError("At least one URL is required")
        if len(v) > MAX_URLS:
            raise ValueError(f"Maximum {MAX_URLS} URLs allowed per request")
        cleaned = []
        for url in v:
            url = url.strip()
            if url:
                cleaned.append(url)
        return cleaned


@app.get("/health")
async def health():
    return {"status": "ok", "message": "Ecommerce Intel API is running"}


@app.get("/health/apify")
async def health_apify():
    """
    Check whether an Apify token is configured and whether the Apify API
    accepts it (GET /v2/users/me). Does not run a browser actor.
    """
    token_set = bool(os.getenv("APIFY_API_TOKEN", "").strip())
    out: dict = {
        "token_configured": token_set,
        "token_preview": apify_fetcher.token_preview_for_logs(),
        "actor": apify_fetcher.ACTOR_ID,
    }
    if not token_set:
        out["api_reachable"] = False
        out["hint"] = "Set APIFY_API_TOKEN in backend/.env and restart uvicorn."
        return out

    ok, err, user = await apify_fetcher.verify_token()
    out["api_reachable"] = ok
    if err:
        out["error"] = err
    if user:
        out["apify_username"] = user.get("username") or user.get("name")
        out["apify_user_id"] = user.get("id")
    return out


@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    """
    Stream analysis results for a list of URLs using Server-Sent Events.
    Each URL is analyzed sequentially and results are streamed as they complete.

    When an Apify API token is configured, the full batch of URLs is first
    rendered via a headless browser (one actor run) so that JS-injected tools
    become visible.  If Apify is unavailable the system falls back to plain
    HTTP fetching.
    """
    urls = request.urls

    async def generate():
        meta = {"type": "meta", "total": len(urls)}
        yield f"data: {json.dumps(meta)}\n\n"

        # ── Batch-fetch rendered HTML from Apify (if enabled/configured) ──────
        rendered_map: dict = {}
        if USE_APIFY and apify_fetcher.is_available():
            try:
                normalized_urls = [normalize_url(u) for u in urls]
                rendered_map = await apify_fetcher.fetch_rendered_html(normalized_urls)
                n_ok = sum(1 for v in rendered_map.values() if v)
                logger.info(
                    "Analyze batch: Apify HTML available for %d / %d URL(s) (map size %d)",
                    n_ok,
                    len(urls),
                    len(rendered_map),
                )
            except Exception as exc:
                logger.warning("Apify batch fetch failed, falling back to httpx: %s", exc)
        else:
            logger.info(
                "Analyze batch: using direct scraper path (httpx only). "
                "Apify code is present but runtime-disabled."
            )

        # ── Analyze each URL (with Apify HTML when available) ─────────
        for i, url in enumerate(urls):
            try:
                norm = normalize_url(url)
                pre_rendered = rendered_map.get(norm)
                if USE_APIFY and apify_fetcher.is_available() and not pre_rendered:
                    logger.warning(
                        "URL %r (normalized %r): no Apify HTML in map — using httpx fallback",
                        url,
                        norm,
                    )
                result = await analyze_url(url, rendered_html=pre_rendered)
                result["type"] = "result"
                result["index"] = i
                yield f"data: {json.dumps(result)}\n\n"
            except Exception as e:
                error_result = {
                    "type": "result",
                    "index": i,
                    "url": url,
                    "status": "error",
                    "error": str(e)[:200],
                    "store_name": url,
                    "domain": url,
                    "platform": None,
                    "email_marketing": [],
                    "sms_marketing": [],
                    "popup_tools": [],
                    "analytics": [],
                    "review_tools": [],
                    "loyalty_tools": [],
                    "subscription_tools": [],
                    "sample_products": [],
                    "industry": None,
                    "description": None,
                    "tech_count": 0,
                    "elapsed_ms": 0,
                    "favicon": "",
                }
                yield f"data: {json.dumps(error_result)}\n\n"

            await asyncio.sleep(0.3)

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.post("/analyze/single")
async def analyze_single(body: dict):
    """Analyze a single URL (non-streaming)."""
    url = body.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    pre_rendered = None
    if USE_APIFY and apify_fetcher.is_available():
        try:
            rendered_map = await apify_fetcher.fetch_rendered_html([normalize_url(url)])
            pre_rendered = rendered_map.get(normalize_url(url))
        except Exception:
            pass

    result = await analyze_url(url, rendered_html=pre_rendered)
    return result
