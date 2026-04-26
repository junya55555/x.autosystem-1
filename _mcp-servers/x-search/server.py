#!/usr/bin/env python3
"""MCP server exposing X (Twitter) v2 search API for Claude Code."""
import os
import sys

import httpx
from mcp.server.fastmcp import FastMCP

X_BEARER_TOKEN = os.environ.get("X_BEARER_TOKEN")
if not X_BEARER_TOKEN:
    print("X_BEARER_TOKEN environment variable is required", file=sys.stderr)
    sys.exit(1)

API_BASE = "https://api.x.com/2"
TWEET_FIELDS = "public_metrics,created_at,author_id,lang"
USER_FIELDS = "username,name"
EXPANSIONS = "author_id"
COST_PER_TWEET_USD = 0.005

http = httpx.Client(
    base_url=API_BASE,
    headers={"Authorization": f"Bearer {X_BEARER_TOKEN}"},
    timeout=30.0,
)

mcp = FastMCP("x-search")


def _format_response(data: dict) -> dict:
    tweets_raw = data.get("data", []) or []
    users_raw = data.get("includes", {}).get("users", []) or []
    users_by_id = {u["id"]: u for u in users_raw}

    tweets = []
    for t in tweets_raw:
        author = users_by_id.get(t.get("author_id"), {})
        username = author.get("username", "")
        tweets.append({
            "id": t["id"],
            "text": t.get("text", ""),
            "created_at": t.get("created_at"),
            "lang": t.get("lang"),
            "author": {
                "id": author.get("id"),
                "username": username,
                "name": author.get("name"),
            },
            "metrics": t.get("public_metrics", {}),
            "url": f"https://x.com/{username}/status/{t['id']}" if username else None,
        })

    meta = data.get("meta", {}) or {}
    result_count = meta.get("result_count", len(tweets))

    return {
        "tweets": tweets,
        "meta": {
            "result_count": result_count,
            "next_token": meta.get("next_token"),
            "newest_id": meta.get("newest_id"),
            "oldest_id": meta.get("oldest_id"),
            "estimated_cost_usd": round(result_count * COST_PER_TWEET_USD, 4),
        },
    }


def _request(path: str, params: dict) -> dict:
    try:
        resp = http.get(path, params=params)
    except httpx.HTTPError as e:
        return {"error": f"network error: {e}"}

    if resp.status_code != 200:
        return {
            "error": f"X API returned HTTP {resp.status_code}",
            "detail": resp.text[:1500],
        }

    return _format_response(resp.json())


@mcp.tool()
def search_x_recent(
    query: str,
    max_results: int = 100,
    next_token: str = "",
) -> dict:
    """Search X posts from the last 7 days.

    Returns tweets with public_metrics (impression_count, like_count, retweet_count,
    reply_count, quote_count, bookmark_count), author info, and post URL.

    Cost: $0.005 per tweet returned (max ~$0.50 per call at max_results=100).

    Args:
        query: X search query syntax. Operators include lang:ja, from:user, has:media,
            has:images, has:videos, -is:retweet, -is:reply. Up to 512 chars.
        max_results: 10-100. Default 100.
        next_token: Pass meta.next_token from a previous call to paginate.
    """
    max_results = max(10, min(100, max_results))
    params = {
        "query": query,
        "max_results": max_results,
        "tweet.fields": TWEET_FIELDS,
        "user.fields": USER_FIELDS,
        "expansions": EXPANSIONS,
    }
    if next_token:
        params["next_token"] = next_token
    return _request("/tweets/search/recent", params)


@mcp.tool()
def search_x_archive(
    query: str,
    max_results: int = 100,
    start_time: str = "",
    end_time: str = "",
    next_token: str = "",
) -> dict:
    """Search X posts across the full archive (back to March 2006).

    Same response format as search_x_recent. Use this for historical research
    or specific date ranges beyond the last 7 days.

    Cost: $0.005 per tweet returned (max ~$2.50 per call at max_results=500).

    Args:
        query: X search query syntax. Up to 1,024 chars.
        max_results: 10-500. Default 100.
        start_time: Optional ISO 8601, e.g. "2024-01-01T00:00:00Z". Inclusive.
        end_time: Optional ISO 8601, e.g. "2024-12-31T23:59:59Z". Exclusive.
        next_token: Pass meta.next_token from a previous call to paginate.
    """
    max_results = max(10, min(500, max_results))
    params = {
        "query": query,
        "max_results": max_results,
        "tweet.fields": TWEET_FIELDS,
        "user.fields": USER_FIELDS,
        "expansions": EXPANSIONS,
    }
    if start_time:
        params["start_time"] = start_time
    if end_time:
        params["end_time"] = end_time
    if next_token:
        params["next_token"] = next_token
    return _request("/tweets/search/all", params)


if __name__ == "__main__":
    mcp.run()
