"""External data connectors for research: Hacker News and GitHub Issues.

Environment variables:
- GITHUB_TOKEN (optional): increases rate limits for GitHub API
"""
from __future__ import annotations
from typing import List, Dict, Optional
import os
import time
import requests
from datetime import datetime

HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search"
GITHUB_SEARCH_ISSUES_URL = "https://api.github.com/search/issues"
APPSTORE_REVIEWS_URL_TMPL = "https://itunes.apple.com/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/json?cc={country}"
ZENDESK_SEARCH_URL_TMPL = "https://{subdomain}.zendesk.com/api/v2/search.json"
INTERCOM_LIST_CONV_URL = "https://api.intercom.io/conversations"
SERPAPI_NEWS_URL = "https://serpapi.com/search.json"


def fetch_hn(query: str, limit: int = 10) -> List[Dict]:
    params = {
        "query": query,
        "tags": "story",
        "hitsPerPage": min(limit, 50),
        "page": 0,
    }
    resp = requests.get(HN_SEARCH_URL, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    items = []
    for hit in data.get("hits", [])[:limit]:
        items.append({
            "source": "hackernews",
            "title": hit.get("title"),
            "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
            "body": hit.get("_highlightResult", {}).get("title", {}).get("value", ""),
            "metadata": {
                "points": hit.get("points"),
                "author": hit.get("author"),
                "created_at": hit.get("created_at"),
            },
        })
    return items


def _source_quality_score(source: Optional[str]) -> int:
    if not source:
        return 0
    source_l = source.lower()
    high = [
        "the verge",
        "the new york times",
        "wsj",
        "bloomberg",
        "reuters",
        "techcrunch",
        "the information",
        "ft",
        "financial times",
        "axios",
        "washington post",
    ]
    med = ["wired", "engadget", "the guardian", "forbes", "cnbc", "venturebeat"]
    if any(s in source_l for s in high):
        return 3
    if any(s in source_l for s in med):
        return 2
    return 1


def fetch_serpapi_news(
    query: str,
    api_key: Optional[str] = None,
    num: int = 10,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    location: str = "United States",
) -> List[Dict]:
    """Fetch Google News via SerpAPI.

    date_from/date_to: 'YYYY-MM-DD' strings for filtering.
    """
    key = api_key or os.getenv("SERPAPI_API_KEY")
    if not key:
        raise ValueError("SERPAPI_API_KEY is required for SerpAPI news.")
    params = {
        "engine": "google_news",
        "q": query,
        "api_key": key,
        "gl": "us",
        "hl": "en",
        "num": min(num, 100),
        "location": location,
    }
    if date_from:
        params["after"] = date_from
    if date_to:
        params["before"] = date_to
    resp = requests.get(SERPAPI_NEWS_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    results = data.get("news_results", [])
    items: List[Dict] = []
    for r in results[:num]:
        source = r.get("source")
        if isinstance(source, dict):
            source = source.get("name")
        items.append({
            "source": "news",
            "title": r.get("title"),
            "url": r.get("link"),
            "body": r.get("snippet") or "",
            "metadata": {
                "date": r.get("date"),
                "source_name": source,
                "quality": _source_quality_score(source),
            },
        })
    return items


def fetch_google_news_rss(query: str, num: int = 10, lang: str = "en", country: str = "US") -> List[Dict]:
    """Fetch Google News via RSS (no key). Requires feedparser to be installed."""
    try:
        import feedparser  # type: ignore
    except Exception:
        raise RuntimeError("feedparser is required for RSS. Install it or use SerpAPI.")
    q = requests.utils.quote(query)
    url = f"https://news.google.com/rss/search?q={q}&hl={lang}-{country}&gl={country}&ceid={country}:{lang}"
    feed = feedparser.parse(url)
    items: List[Dict] = []
    for e in feed.entries[:num]:
        title = e.get("title")
        link = e.get("link")
        summary = e.get("summary")
        source = None
        if hasattr(e, "source") and getattr(e, "source"):
            source = getattr(e.source, "title", None)
        items.append({
            "source": "news",
            "title": title,
            "url": link,
            "body": summary or "",
            "metadata": {
                "source_name": source,
                "quality": _source_quality_score(source),
            },
        })
    return items


def fetch_appstore_reviews(app_id: str, country: str = "us", pages: int = 1, limit: int = 20) -> List[Dict]:
    """Fetch recent App Store reviews via Apple's RSS feed.

    Note: Apple returns at most ~50 reviews per page. This is a best-effort public
    feed and may vary by region/app.
    """
    items: List[Dict] = []
    fetched = 0
    for page in range(1, max(1, pages) + 1):
        url = APPSTORE_REVIEWS_URL_TMPL.format(page=page, app_id=app_id, country=country)
        try:
            resp = requests.get(url, timeout=20)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            break
        entries = data.get("feed", {}).get("entry", [])
        # The first entry can be app metadata, skip if it lacks 'im:rating'
        for entry in entries:
            if "im:rating" not in entry:
                continue
            title = entry.get("title", {}).get("label")
            content = entry.get("content", {}).get("label", "")
            rating = entry.get("im:rating", {}).get("label")
            author = entry.get("author", {}).get("name", {}).get("label")
            updated = entry.get("updated", {}).get("label")
            items.append({
                "source": "appstore",
                "title": title,
                "url": None,  # reviews aren't individually addressable via URL in RSS
                "body": content,
                "metadata": {
                    "rating": rating,
                    "author": author,
                    "updated": updated,
                    "app_id": app_id,
                    "country": country,
                },
            })
            fetched += 1
            if fetched >= limit:
                return items
    return items


def fetch_github_issues(repo: str, query: Optional[str] = None, limit: int = 10, token: Optional[str] = None) -> List[Dict]:
    headers = {"Accept": "application/vnd.github+json"}
    token = token or os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    q = f"repo:{repo}"
    if query:
        q += f" {query}"
    params = {
        "q": q,
        "per_page": min(limit, 50),
        "page": 1,
        "sort": "created",
        "order": "desc",
    }
    resp = requests.get(GITHUB_SEARCH_ISSUES_URL, headers=headers, params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    items = []
    for it in data.get("items", [])[:limit]:
        items.append({
            "source": "github",
            "title": it.get("title"),
            "url": it.get("html_url"),
            "body": it.get("body") or "",
            "metadata": {
                "state": it.get("state"),
                "comments": it.get("comments"),
                "created_at": it.get("created_at"),
                "updated_at": it.get("updated_at"),
            },
        })
    return items


def fetch_zendesk_tickets(
    subdomain: str,
    email: str,
    api_token: str,
    query: str = "type:ticket status<solved",
    limit: int = 20,
) -> List[Dict]:
    """Fetch Zendesk tickets via the Search API.

    Auth: Basic auth with username "{email}/token" and password "{api_token}".
    """
    url = ZENDESK_SEARCH_URL_TMPL.format(subdomain=subdomain)
    auth = (f"{email}/token", api_token)
    params = {
        "query": query,
        "per_page": min(limit, 100),
        "page": 1,
    }
    resp = requests.get(url, params=params, auth=auth, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    items: List[Dict] = []
    for res in data.get("results", [])[:limit]:
        if res.get("result_type") != "ticket":
            continue
        items.append(
            {
                "source": "zendesk",
                "title": res.get("subject"),
                "url": None,
                "body": res.get("description"),
                "metadata": {
                    "status": res.get("status"),
                    "priority": res.get("priority"),
                    "created_at": res.get("created_at"),
                    "updated_at": res.get("updated_at"),
                    "id": res.get("id"),
                },
            }
        )
    return items


def fetch_intercom_conversations(
    access_token: str,
    state: str = "open",
    limit: int = 20,
) -> List[Dict]:
    """Fetch Intercom conversations.

    Requires a Personal Access Token. Docs: https://developers.intercom.com/intercom-api-reference/reference
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    params = {
        "display_as": "plaintext",
        "per_page": min(limit, 60),
        "state": state,
    }
    resp = requests.get(INTERCOM_LIST_CONV_URL, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    items: List[Dict] = []
    for conv in data.get("conversations", [])[:limit]:
        title = conv.get("title") or f"Conversation {conv.get('id')}"
        body = conv.get("teammate_summary") or ""
        url = None
        items.append(
            {
                "source": "intercom",
                "title": title,
                "url": url,
                "body": body,
                "metadata": {
                    "state": conv.get("state"),
                    "created_at": conv.get("created_at"),
                    "updated_at": conv.get("updated_at"),
                    "id": conv.get("id"),
                },
            }
        )
    return items
