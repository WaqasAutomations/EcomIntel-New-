"""
Apify integration for JS-rendered page fetching.

Uses the apify/web-scraper actor (headless Chromium) to render pages and
return the full post-JS DOM.  Falls back gracefully when no API token is
configured or when credits are exhausted.

Dataset items are keyed by Apify's final URL (after redirects); we map them
back to the caller's URLs using a canonical key so www/http/https/trailing
slashes all match.
"""

import os
import time
import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

from apify_client import ApifyClient
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

ACTOR_ID = "apify/web-scraper"

# Use setTimeout instead of page.waitForTimeout — the latter was removed in
# newer Puppeteer and breaks the actor with a runtime error.
PAGE_FUNCTION = """
async function pageFunction(context) {
    const { request, page } = context;
    await new Promise(function(resolve) { setTimeout(resolve, 6000); });
    const html = await page.content();
    return {
        url: request.url,
        html: html,
    };
}
"""

ACTOR_TIMEOUT_SECS = 180


def token_preview_for_logs() -> str:
    t = (os.getenv("APIFY_API_TOKEN") or "").strip()
    if not t:
        return "(not set)"
    if len(t) <= 12:
        return t[:4] + "…"
    return t[:8] + "…" + t[-4:]


def canonical_match_key(url: str) -> str:
    """
    Normalize URL for matching Apify's post-redirect URL to our requested URL.
    Handles http/https, www, trailing slashes, default ports.
    """
    u = (url or "").strip()
    if not u.startswith(("http://", "https://")):
        u = "https://" + u
    p = urlparse(u)
    scheme = (p.scheme or "https").lower()
    if scheme in ("http", "https"):
        scheme = "https"
    host = (p.netloc or "").lower()
    if ":" in host:
        h, _, port = host.rpartition(":")
        if port in ("80", "443"):
            host = h
    if host.startswith("www."):
        host = host[4:]
    path = (p.path or "").rstrip("/") or ""
    query = p.query
    if query:
        return f"{scheme}://{host}{path}?{query}"
    return f"{scheme}://{host}{path}"


def is_available() -> bool:
    """Return True if Apify integration is configured and usable."""
    return bool(os.getenv("APIFY_API_TOKEN", "").strip())


async def verify_token() -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Call Apify API to verify the token (lightweight user lookup).
    Returns (ok, error_message_or_none, user_dict_or_none).
    """
    token = (os.getenv("APIFY_API_TOKEN") or "").strip()
    if not token:
        return False, "APIFY_API_TOKEN is empty", None

    def _call() -> Dict[str, Any]:
        return ApifyClient(token=token).user().get()

    try:
        user = await asyncio.to_thread(_call)
        return True, None, user
    except Exception as exc:
        return False, str(exc), None


async def fetch_rendered_html(urls: List[str]) -> Dict[str, Optional[str]]:
    """
    Run the apify/web-scraper actor on a batch of URLs and return a mapping
    of *each requested URL string* -> rendered HTML (or None if no match).

    Keys in the returned dict match the `urls` list entries exactly so
    callers can use normalize_url(user_input) as the lookup key.
    """
    token = (os.getenv("APIFY_API_TOKEN") or "").strip()
    if not token:
        logger.warning(
            "Apify: skip fetch — APIFY_API_TOKEN not set (load backend/.env)."
        )
        return {}

    if not urls:
        return {}

    logger.info(
        "Apify: starting actor %s for %d URL(s); token=%s",
        ACTOR_ID,
        len(urls),
        token_preview_for_logs(),
    )
    for i, u in enumerate(urls[:10]):
        logger.info("Apify:   [%d] %r → canonical %r", i, u, canonical_match_key(u))
    if len(urls) > 10:
        logger.info("Apify:   … and %d more URLs", len(urls) - 10)

    client = ApifyClient(token=token)

    start_urls = [{"url": u} for u in urls]

    run_input: Dict[str, Any] = {
        "startUrls": start_urls,
        "pageFunction": PAGE_FUNCTION,
        "maxPagesPerCrawl": len(urls),
        "maxConcurrency": 3,
        "pageLoadTimeoutSecs": 60,
        "maxRequestRetries": 2,
        "ignoreSslErrors": True,
    }

    use_proxy = os.getenv("APIFY_USE_PROXY", "true").lower() in (
        "1",
        "true",
        "yes",
    )
    if use_proxy:
        run_input["proxyConfiguration"] = {"useApifyProxy": True}
        logger.info("Apify: using Apify datacenter proxy (set APIFY_USE_PROXY=false to disable)")
    else:
        logger.info("Apify: proxy disabled (APIFY_USE_PROXY=false)")

    t0 = time.perf_counter()
    try:
        run = await asyncio.to_thread(
            client.actor(ACTOR_ID).call,
            run_input=run_input,
            timeout_secs=ACTOR_TIMEOUT_SECS,
        )
    except Exception as exc:
        logger.error("Apify: actor .call() failed after %.1fs: %s", time.perf_counter() - t0, exc)
        return {}

    elapsed = time.perf_counter() - t0
    if not run:
        logger.error("Apify: actor returned empty run object after %.1fs", elapsed)
        return {}

    run_id = run.get("id")
    status = run.get("status")
    dataset_id = run.get("defaultDatasetId")
    logger.info(
        "Apify: run finished in %.1fs — id=%s status=%s dataset=%s",
        elapsed,
        run_id,
        status,
        dataset_id,
    )

    st = str(status or "").upper()
    if st in ("FAILED", "ABORTED", "TIMED-OUT", "TIMED_OUT"):
        logger.error("Apify: run ended with status %r — check run %s in Apify console", status, run_id)

    if not dataset_id:
        logger.error("Apify: no defaultDatasetId on run; cannot read HTML")
        return {}

    canonical_to_html: Dict[str, str] = {}
    item_index = 0
    try:
        for item in client.dataset(dataset_id).iterate_items():
            item_index += 1
            item_url = item.get("url")
            item_html = item.get("html")
            err = item.get("error") or item.get("errorMessage")

            if err and not item_html:
                logger.warning(
                    "Apify: dataset item #%d url=%r error=%r (no html)",
                    item_index,
                    item_url,
                    err,
                )
                continue

            if not item_url or not item_html:
                keys = list(item.keys()) if isinstance(item, dict) else []
                logger.warning(
                    "Apify: dataset item #%d missing url/html; keys=%s",
                    item_index,
                    keys,
                )
                continue

            ck = canonical_match_key(item_url)
            prev = canonical_to_html.get(ck)
            if prev is None or len(item_html) > len(prev):
                canonical_to_html[ck] = item_html
            logger.info(
                "Apify: dataset item #%d url=%r canonical=%r html_chars=%d",
                item_index,
                item_url,
                ck,
                len(item_html),
            )
    except Exception as exc:
        logger.error("Apify: dataset iterate_items failed: %s", exc)
        return {}

    if not canonical_to_html:
        logger.error(
            "Apify: dataset had %d raw item(s) but no usable html rows",
            item_index,
        )

    logger.info(
        "Apify: canonical keys from dataset (%d): %s",
        len(canonical_to_html),
        list(canonical_to_html.keys())[:15],
    )

    result: Dict[str, Optional[str]] = {}
    matched = 0
    for req in urls:
        ck = canonical_match_key(req)
        html = canonical_to_html.get(ck)
        if html is None:
            logger.warning(
                "Apify: NO MATCH for requested URL %r (canonical %r). "
                "Dataset had %d canonical key(s).",
                req,
                ck,
                len(canonical_to_html),
            )
        else:
            matched += 1
            logger.info(
                "Apify: MATCH %r → %d chars html",
                req,
                len(html),
            )
        result[req] = html

    logger.info(
        "Apify: summary — matched %d / %d requested URLs with rendered HTML",
        matched,
        len(urls),
    )
    return result
