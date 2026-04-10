import httpx
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import json
import re
from typing import Optional, List, Dict, Any
import time

# ─── Signal Dictionaries ──────────────────────────────────────────────────────

PLATFORM_SIGNALS = {
    "Shopify": [
        "cdn.shopify.com", "myshopify.com", "Shopify.shop", "shopify-section",
        "window.Shopify", "__st/", "shopify_currency", "Shopify.theme",
        "shopify-payment-button", "ShopifyAnalytics"
    ],
    "WooCommerce": [
        "woocommerce", "wp-content/plugins/woocommerce", "wc-api", "wc_add_to_cart",
        "woocommerce-page", "wp-json/wc/"
    ],
    "BigCommerce": [
        "bigcommerce.com", "cdn11.bigcommerce.com", "BigCommerce", "bc-sf-filter",
        "BCData", "Bigcommerce"
    ],
    "Magento": [
        "mage/", "Magento_", "Mage.Cookies", "magento/", "requirejs/require.js",
        "adminhtml/Magento"
    ],
    "Squarespace": [
        "squarespace.com", "static.squarespace.com", "squarespace-cdn.com",
        "sqs-video", "squarespace"
    ],
    "Wix": [
        "wix.com", "wixsite.com", "static.parastorage.com", "wix-code",
        "_wix_", "wixstatic.com"
    ],
    "Webflow": [
        "webflow.com", "assets.website-files.com", "uploads-ssl.webflow.com",
        "data-wf-page", "wf-form"
    ],
    "Salesforce Commerce Cloud": [
        "demandware.net", "salesforce.com/cci", "sfcc", "demandware"
    ],
    "Prestashop": ["prestashop", "presta_", "id_product"],
    "OpenCart": ["catalog/view/theme", "route=product", "opencart"],
    "Shopware": ["shopware", "sw-plugin", "storefront/main"],
    "SAP Hybris": ["hybris", "acceleratorstorefronts"],
}

EMAIL_SIGNALS = {
    "Klaviyo": ["klaviyo.com", "klaviyo", "KlaviyoSubscribe", "__kl_", "_learnq"],
    "Mailchimp": [
        "mailchimp.com", "chimpstatic.com", "list-manage.com", "mc.us",
        "mailchi.mp", "us1.list-manage"
    ],
    "Omnisend": ["omnisend.com", "omnisend", "omnisend-signup"],
    "Drip": ["getdrip.com", "drip.com", "_dc_gtm"],
    "HubSpot": ["hubspot.com", "hs-scripts.com", "hsforms", "hbspt"],
    "Brevo / Sendinblue": ["sendinblue.com", "sibforms.com", "brevo.com"],
    "ActiveCampaign": ["activecampaign.com", "trackcmp.net"],
    "Postmark": ["postmarkapp.com"],
    "SendGrid": ["sendgrid.net", "sendgrid.com"],
    "Constant Contact": ["constantcontact.com", "r20.rs6.net"],
    "Campaign Monitor": ["campaignmonitor.com", "createsend.com"],
    "Listrak": ["listrak.com", "listrakbi.com"],
    "Dotdigital": ["dotdigital.com", "dotmailer.com"],
}

SMS_SIGNALS = {
    "Attentive": ["attentivemobile.com", "attn.tv", "cdn.attn.tv"],
    "Postscript": ["postscript.io", "postscript"],
    "Klaviyo SMS": ["klaviyo.com/sms", "klaviyo_sms", "sms_signup"],
    "SMSBump": ["smsbump.com", "smsbump"],
    "Yotpo SMS": ["yotpo.com/sms"],
    "Recart": ["recart.com"],
    "Slicktext": ["slicktext.com"],
    "SimpleTexting": ["simpletexting.com"],
    "Emotive": ["emotivecorp.com"],
    "Cartloop": ["cartloop.io"],
}

POPUP_SIGNALS = {
    "Privy": ["privy.com", "widget.privy.com", "s.privy.com"],
    "Justuno": ["justuno.com", "cdn.jst.ai", "justuno"],
    "Klaviyo Forms": ["a.klaviyo.com", "klaviyo_subscribe", "klaviyo-form"],
    "OptinMonster": ["optinmonster.com", "omwdt.com"],
    "Wheelio": ["wheelio.com", "wheelio"],
    "Spin-a-Sale": ["spin-a-sale.com"],
    "Gorgias": ["gorgias.com", "config.gorgias.chat", "gorgias-chat"],
    "Tidio": ["tidio.com", "tidiochat"],
    "Intercom": ["intercom.io", "widget.intercom.io", "intercomcdn.com"],
    "Zendesk": ["zendesk.com", "zopim.com", "ekr.zdassets.com"],
    "Freshdesk": ["freshdesk.com", "freshwidget"],
    "Drift": ["drift.com", "js.driftt.com"],
    "LiveChat": ["livechatinc.com", "cdn.livechat.com"],
    "Bold Chat": ["boldchat.com"],
    "Hubspot Chat": ["hs-banner.com", "hubspot chat"],
}

ANALYTICS_SIGNALS = {
    "Google Analytics 4": ["gtag.js", "G-", "googletagmanager.com", "ga4"],
    "Google Tag Manager": ["googletagmanager.com", "GTM-"],
    "Facebook Pixel": ["connect.facebook.net", "fbevents.js", "fbq("],
    "TikTok Pixel": ["analytics.tiktok.com", "ttq."],
    "Pinterest Tag": ["pintrk", "pinterest.com/ct.js", "pinit.js"],
    "Snapchat Pixel": ["sc-static.net", "snaptr"],
    "Twitter Pixel": ["static.ads-twitter.com", "twq("],
    "Hotjar": ["hotjar.com", "static.hotjar.com", "hj("],
    "Heap": ["heapanalytics.com", "heap.io"],
    "Segment": ["segment.com", "analytics.min.js", "cdn.segment.com"],
    "Mixpanel": ["mixpanel.com", "cdn.mxpnl.com"],
    "Amplitude": ["amplitude.com", "cdn.amplitude.com"],
    "Microsoft Clarity": ["clarity.ms", "c.clarity.ms"],
    "Lucky Orange": ["luckyorange.com"],
    "FullStory": ["fullstory.com", "fullstory"],
    "Datadog RUM": ["datadoghq.com/browser"],
    "Northbeam": ["northbeam.io"],
    "Triple Whale": ["triplewhale.com"],
    "Elevar": ["getelevar.com"],
}

REVIEW_SIGNALS = {
    "Yotpo Reviews": ["staticw2.yotpo.com", "yotpo.com/widget", "yotpo_reviews"],
    "Judge.me": ["judge.me", "cdn.judge.me"],
    "Loox": ["loox.io", "loox.app", "looxcdn"],
    "Stamped.io": ["stamped.io", "stampedinc"],
    "Okendo": ["okendo.io", "okendo"],
    "Bazaarvoice": ["bazaarvoice.com"],
    "PowerReviews": ["powerreviews.com"],
    "Trustpilot": ["trustpilot.com", "tp.trustpilot"],
    "Reviews.io": ["reviews.io", "widget.reviews.io"],
    "Junip": ["junip.co"],
}

LOYALTY_SIGNALS = {
    "Smile.io": ["smile.io", "cdn.smile.io", "smile-ui"],
    "LoyaltyLion": ["loyaltylion.com", "loyaltylion"],
    "Yotpo Loyalty": ["loyalty.yotpo.com"],
    "Marsello": ["marsello.com"],
    "Growave": ["growave.io", "ssw.secomapp"],
}

SUBSCRIPTION_SIGNALS = {
    "ReCharge": ["rechargeapps.com", "rechargepayments.com", "recharge"],
    "Bold Subscriptions": ["boldapps.net/subscriptions"],
    "Skio": ["skio.com"],
    "Ordergroove": ["ordergroove.com"],
    "Stay AI": ["withstay.com"],
    "Loop Subscriptions": ["loopwork.co"],
}

# ─── Industry Keyword Map ─────────────────────────────────────────────────────

INDUSTRY_KEYWORDS = {
    "Apparel & Fashion": [
        "clothing", "apparel", "fashion", "shirt", "pants", "dress", "jacket",
        "hoodie", "jeans", "wear", "outfit", "style", "garment", "tee", "shorts",
        "sweater", "activewear", "athleisure", "streetwear"
    ],
    "Footwear": [
        "shoe", "sneaker", "boot", "footwear", "sandal", "loafer", "slipper",
        "heel", "insole", "running shoe"
    ],
    "Beauty & Skincare": [
        "skincare", "beauty", "makeup", "cosmetic", "serum", "moisturizer",
        "foundation", "lipstick", "cleanser", "toner", "sunscreen", "blush",
        "mascara", "eyeshadow", "concealer", "glow", "skin"
    ],
    "Food & Beverage": [
        "food", "snack", "drink", "coffee", "tea", "beverage", "organic",
        "nutrition", "protein", "supplement", "healthy", "eat", "meal",
        "sauce", "spice", "chocolate", "candy", "jerky", "chip", "popcorn",
        "tinned", "canned", "fish", "seafood"
    ],
    "Fitness & Wellness": [
        "fitness", "gym", "workout", "exercise", "health", "wellness", "yoga",
        "supplement", "protein powder", "pre-workout", "crossfit", "training"
    ],
    "Home & Living": [
        "home", "furniture", "decor", "kitchen", "bedding", "pillow", "rug",
        "towel", "sheet", "tableware", "cookware", "storage", "interior"
    ],
    "Jewelry & Accessories": [
        "jewelry", "jewellery", "bracelet", "necklace", "ring", "earring",
        "watch", "accessory", "gemstone", "gold", "silver", "charm"
    ],
    "Consumer Electronics": [
        "headphone", "speaker", "audio", "electronic", "tech", "gadget",
        "wireless", "bluetooth", "earphone", "earbuds", "device", "charger"
    ],
    "Outdoor & Sports": [
        "outdoor", "hiking", "camping", "ski", "snowboard", "surf", "sport",
        "adventure", "trail", "mountain", "cycling", "fishing", "hunting"
    ],
    "Pet Products": [
        "pet", "dog", "cat", "puppy", "kitten", "treat", "collar", "leash",
        "bowl", "toy for pet", "veterinary"
    ],
    "Baby & Kids": [
        "baby", "toddler", "kids", "children", "nursery", "diaper", "stroller",
        "pacifier", "feeding"
    ],
    "Hair Care": [
        "hair", "shampoo", "conditioner", "haircare", "scalp", "beard", "grooming",
        "hair loss", "hair growth"
    ],
}

# ─── HTTP Client Config ───────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}


# ─── Helper Functions ─────────────────────────────────────────────────────────

def _uniq_keep_order(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for x in items:
        if not x:
            continue
        if x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out


def _base_origin(url: str) -> str:
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}"


def _safe_join(base: str, maybe_url: str) -> Optional[str]:
    if not maybe_url:
        return None
    u = maybe_url.strip()
    if not u:
        return None
    if u.startswith("//"):
        return "https:" + u
    if u.startswith("http://") or u.startswith("https://"):
        return u
    return urljoin(base, u)


def extract_script_srcs(soup: BeautifulSoup, base_url: str) -> List[str]:
    srcs: List[str] = []
    for tag in soup.find_all("script"):
        src = tag.get("src")
        full = _safe_join(base_url, src) if src else None
        if full:
            srcs.append(full)
    return _uniq_keep_order(srcs)


def normalize_url(url: str) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url.rstrip("/")


def extract_domain(url: str) -> str:
    return urlparse(url).netloc.replace("www.", "")


def detect_tools(content: str, signal_map: dict) -> List[str]:
    detected = []
    content_lower = content.lower()
    for tool, patterns in signal_map.items():
        for pattern in patterns:
            if pattern.lower() in content_lower:
                detected.append(tool)
                break
    return detected


def detect_platform(html: str, soup: BeautifulSoup, response_headers: dict) -> str:
    # Check meta generator tag
    meta_gen = soup.find("meta", attrs={"name": "generator"})
    if meta_gen:
        content = (meta_gen.get("content") or "").lower()
        for platform, patterns in PLATFORM_SIGNALS.items():
            for p in patterns:
                if p.lower() in content:
                    return platform

    # Check HTML content
    for platform, patterns in PLATFORM_SIGNALS.items():
        for pattern in patterns:
            if pattern in html:
                return platform

    # Check server header
    server = response_headers.get("server", "").lower()
    if "shopify" in server:
        return "Shopify"

    return "Custom / Unknown"


def extract_store_name(soup: BeautifulSoup, url: str) -> str:
    # Try OG site name
    og_site = soup.find("meta", property="og:site_name")
    if og_site and og_site.get("content"):
        return og_site["content"].strip()

    # Try title tag
    title = soup.find("title")
    if title and title.text:
        t = title.text.strip()
        # Remove common suffixes
        for sep in [" – ", " | ", " - ", " · "]:
            if sep in t:
                return t.split(sep)[0].strip()
        return t[:60]

    return extract_domain(url).title()


def extract_description(soup: BeautifulSoup) -> Optional[str]:
    # OG description first
    og_desc = soup.find("meta", property="og:description")
    if og_desc and og_desc.get("content"):
        return og_desc["content"].strip()[:200]

    # Meta description
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        return meta_desc["content"].strip()[:200]

    return None


def infer_industry(soup: BeautifulSoup, html: str, products: List[str]) -> str:
    """Infer store industry from page content and products."""
    # Combine all text signals
    text_sources = []

    desc = extract_description(soup)
    if desc:
        text_sources.append(desc.lower())

    title = soup.find("title")
    if title:
        text_sources.append(title.text.lower())

    # Add product names
    text_sources.extend([p.lower() for p in products])

    # Page body text (limited)
    body_text = soup.get_text(separator=" ", strip=True)[:2000].lower()
    text_sources.append(body_text)

    combined = " ".join(text_sources)

    # Score each industry
    scores: Dict[str, int] = {}
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        score = sum(combined.count(kw) for kw in keywords)
        if score > 0:
            scores[industry] = score

    if scores:
        return max(scores, key=scores.get)

    return "General E-commerce"


def extract_products_from_html(soup: BeautifulSoup) -> List[str]:
    """Extract product names from HTML schema or OG tags."""
    products = []

    # Schema.org Product
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        try:
            data = json.loads(script.string or "")
            if isinstance(data, dict):
                data = [data]
            for item in data:
                if isinstance(item, dict):
                    if item.get("@type") == "Product":
                        name = item.get("name")
                        if name and name not in products:
                            products.append(name)
                    # ItemList
                    if item.get("@type") == "ItemList":
                        for elem in item.get("itemListElement", []):
                            if isinstance(elem, dict):
                                n = elem.get("name") or (elem.get("item") or {}).get("name")
                                if n and n not in products:
                                    products.append(n)
        except Exception:
            pass

    # OG title as product hint
    if not products:
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            products.append(og_title["content"].strip())

    return products[:6]


def get_favicon_url(soup: BeautifulSoup, base_url: str) -> Optional[str]:
    # Try link tags
    for rel in ["shortcut icon", "icon", "apple-touch-icon"]:
        link = soup.find("link", rel=lambda r: r and rel in r)
        if link and link.get("href"):
            href = link["href"]
            if href.startswith("http"):
                return href
            return urljoin(base_url, href)

    # Default favicon
    domain = urlparse(base_url).scheme + "://" + urlparse(base_url).netloc
    return f"{domain}/favicon.ico"


# ─── Shopify Product Fetch ────────────────────────────────────────────────────

async def fetch_shopify_products(base_url: str, client: httpx.AsyncClient) -> List[str]:
    try:
        products_url = base_url.rstrip("/") + "/products.json?limit=6"
        resp = await client.get(products_url, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            products = data.get("products", [])
            return [p["title"] for p in products[:6] if p.get("title")]
    except Exception:
        pass
    return []


# ─── Main Fetch ───────────────────────────────────────────────────────────────

async def fetch_page(url: str, client: httpx.AsyncClient):
    resp = await client.get(url, timeout=15, follow_redirects=True)
    # Some storefronts return 403/404 to non-browser clients but still serve HTML
    # that we can parse for tech signals. Treat 5xx as fatal; otherwise continue.
    if resp.status_code >= 500:
        resp.raise_for_status()
    return resp.text, dict(resp.headers), str(resp.url), resp.status_code, resp.reason_phrase


async def fetch_best_effort_text(url: str, client: httpx.AsyncClient, timeout_s: float = 10.0) -> Optional[str]:
    """Fetch a URL and return text even for most 4xx responses (best-effort)."""
    try:
        resp = await client.get(url, timeout=timeout_s, follow_redirects=True)
        # For our purposes, we can often still parse HTML on 403/404, but 5xx tends to be noise.
        if resp.status_code >= 500:
            return None
        return resp.text or ""
    except Exception:
        return None


async def fetch_best_effort_bytes(
    url: str,
    client: httpx.AsyncClient,
    timeout_s: float = 10.0,
    max_bytes: int = 1_500_000,
) -> Optional[str]:
    """Fetch a URL and return decoded body (truncated) best-effort."""
    try:
        resp = await client.get(url, timeout=timeout_s, follow_redirects=True)
        if resp.status_code >= 500:
            return None
        content = resp.content[:max_bytes]
        # try to decode as utf-8; fall back to latin-1 to avoid exceptions
        try:
            return content.decode("utf-8", errors="ignore")
        except Exception:
            return content.decode("latin-1", errors="ignore")
    except Exception:
        return None


async def _enrich_html_with_script_bodies(
    combined_html: str,
    soup: BeautifulSoup,
    origin: str,
    client: httpx.AsyncClient,
    max_scripts: int = 10,
) -> str:
    """Append fetched JS bundle text so substring tool detection sees minified vendors."""
    script_srcs = extract_script_srcs(soup, origin)
    prioritized: List[str] = []
    vendor_keys = [
        "klaviyo", "yotpo", "attentive", "postscript", "gorgias", "zendesk",
        "intercom", "judge.me", "stamped", "okendo", "hotjar", "gtm",
        "googletagmanager", "facebook", "tiktok", "segment", "mailchimp",
        "omnisend", "recharge", "skio", "smile.io", "loyaltylion",
    ]
    for s in script_srcs:
        ls = s.lower()
        if any(k in ls for k in vendor_keys):
            prioritized.append(s)
    for s in script_srcs:
        if s not in prioritized:
            prioritized.append(s)
        if len(prioritized) >= max_scripts:
            break
    script_texts = await asyncio.gather(
        *[
            fetch_best_effort_bytes(u, client, timeout_s=12.0, max_bytes=1_500_000)
            for u in prioritized[:max_scripts]
        ]
    )
    extra = "\n\n".join([t for t in script_texts if t])
    if not extra:
        return combined_html
    return combined_html + "\n\n" + extra


async def fetch_generic_products(origin: str, client: httpx.AsyncClient) -> List[str]:
    """
    Best-effort product sampling for common platforms.
    - Shopify: /products.json
    - WooCommerce: /wp-json/wc/store/products
    """
    # Shopify
    try:
        r = await client.get(f"{origin}/products.json?limit=6", timeout=8, follow_redirects=True)
        if r.status_code == 200:
            data = r.json()
            products = data.get("products", [])
            titles = [p.get("title") for p in products[:6] if isinstance(p, dict)]
            titles = [t for t in titles if isinstance(t, str) and t.strip()]
            if titles:
                return _uniq_keep_order(titles)[:6]
    except Exception:
        pass

    # WooCommerce Store API (public)
    try:
        r = await client.get(f"{origin}/wp-json/wc/store/products?per_page=6", timeout=8, follow_redirects=True)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list):
                titles = []
                for p in data[:6]:
                    if isinstance(p, dict):
                        name = p.get("name")
                        if isinstance(name, str) and name.strip():
                            titles.append(name.strip())
                if titles:
                    return _uniq_keep_order(titles)[:6]
    except Exception:
        pass

    return []


# ─── Core Analyzer ───────────────────────────────────────────────────────────

async def analyze_url(url: str, rendered_html: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze a single ecommerce URL.

    If *rendered_html* is provided (from Apify headless browser), it is used as
    the primary HTML source and the httpx multi-page crawl is skipped.  When it
    is ``None``, we fall back to the original httpx-based fetching strategy.
    """
    normalized = normalize_url(url)
    domain = extract_domain(normalized)
    start_time = time.time()

    result: Dict[str, Any] = {
        "url": url,
        "normalized_url": normalized,
        "domain": domain,
        "status": "success",
        "store_name": domain.title(),
        "favicon": f"https://www.google.com/s2/favicons?domain={domain}&sz=64",
        "platform": None,
        "description": None,
        "industry": "General E-commerce",
        "sample_products": [],
        "email_marketing": [],
        "sms_marketing": [],
        "popup_tools": [],
        "analytics": [],
        "review_tools": [],
        "loyalty_tools": [],
        "subscription_tools": [],
        "tech_count": 0,
        "error": None,
        "elapsed_ms": 0,
        "render_source": "httpx",
        "apify_html_chars": 0,
    }

    try:
        limits = httpx.Limits(max_connections=20, max_keepalive_connections=10)
        async with httpx.AsyncClient(
            headers=HEADERS,
            verify=False,
            limits=limits,
            timeout=httpx.Timeout(15.0, connect=8.0),
        ) as client:

            # ── Obtain the main HTML ──────────────────────────────────────
            if rendered_html:
                # Apify already gave us JS-rendered DOM; use it directly.
                html = rendered_html
                resp_headers: dict = {}
                final_url = normalized
                origin = _base_origin(normalized)
            else:
                # Fallback: plain HTTP fetch + multi-page crawl.
                html, resp_headers, final_url, status_code, reason = await fetch_page(normalized, client)
                origin = _base_origin(final_url)

                if status_code >= 400:
                    result["status"] = "http_error"
                    result["error"] = f"HTTP {status_code}: {reason}"

            soup = BeautifulSoup(html, "lxml")

            # ── Enrich HTML for detection ─────────────────────────────────
            if rendered_html:
                result["render_source"] = "apify"
                result["apify_html_chars"] = len(rendered_html)
                combined_html = html
                combined_html = await _enrich_html_with_script_bodies(
                    combined_html, soup, origin, client, max_scripts=12
                )
            else:
                extra_paths = [
                    "/products",
                    "/collections",
                    "/cart",
                    "/pages/contact",
                    "/contact",
                    "/about",
                    "/privacy-policy",
                    "/terms-of-service",
                ]
                extra_urls = [origin + p for p in extra_paths]
                extra_htmls = await asyncio.gather(
                    *[fetch_best_effort_text(u, client, timeout_s=8.0) for u in extra_urls]
                )
                combined_html = "\n\n".join([html] + [h for h in extra_htmls if h])
                tmp_soup = BeautifulSoup(combined_html, "lxml")
                combined_html = await _enrich_html_with_script_bodies(
                    combined_html, tmp_soup, origin, client, max_scripts=6
                )

            combined_soup = BeautifulSoup(combined_html, "lxml")

            # ── Extract base info ─────────────────────────────────────────
            result["store_name"] = extract_store_name(soup, final_url)
            result["description"] = extract_description(soup)
            result["platform"] = detect_platform(combined_html, combined_soup, resp_headers)
            fav = get_favicon_url(soup, origin)
            if fav:
                result["favicon"] = fav

            # ── Detect all tech signals ───────────────────────────────────
            result["email_marketing"] = detect_tools(combined_html, EMAIL_SIGNALS)
            result["sms_marketing"] = detect_tools(combined_html, SMS_SIGNALS)
            result["popup_tools"] = detect_tools(combined_html, POPUP_SIGNALS)
            result["analytics"] = detect_tools(combined_html, ANALYTICS_SIGNALS)
            result["review_tools"] = detect_tools(combined_html, REVIEW_SIGNALS)
            result["loyalty_tools"] = detect_tools(combined_html, LOYALTY_SIGNALS)
            result["subscription_tools"] = detect_tools(combined_html, SUBSCRIPTION_SIGNALS)

            # ── Get products ──────────────────────────────────────────────
            if result["platform"] == "Shopify":
                async with httpx.AsyncClient(
                    headers=HEADERS, verify=False,
                    timeout=httpx.Timeout(10.0)
                ) as prod_client:
                    result["sample_products"] = await fetch_shopify_products(
                        normalized, prod_client
                    )

            if not result["sample_products"]:
                result["sample_products"] = await fetch_generic_products(origin, client)

            if not result["sample_products"]:
                result["sample_products"] = extract_products_from_html(combined_soup)

            # ── Infer industry ────────────────────────────────────────────
            result["industry"] = infer_industry(combined_soup, combined_html, result["sample_products"])

            # ── Total tech count ──────────────────────────────────────────
            result["tech_count"] = sum([
                len(result["email_marketing"]),
                len(result["sms_marketing"]),
                len(result["popup_tools"]),
                len(result["analytics"]),
                len(result["review_tools"]),
                len(result["loyalty_tools"]),
                len(result["subscription_tools"]),
            ])

    except httpx.TimeoutException:
        result["status"] = "timeout"
        result["error"] = "Request timed out after 15 seconds"
    except httpx.HTTPStatusError as e:
        result["status"] = "http_error"
        result["error"] = f"HTTP {e.response.status_code}: {e.response.reason_phrase}"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)[:200]

    result["elapsed_ms"] = round((time.time() - start_time) * 1000)
    if rendered_html and not rendered_html.strip():
        result["render_source"] = "httpx"
        result["apify_html_chars"] = 0
    return result
