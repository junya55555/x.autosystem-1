#!/usr/bin/env python3
"""MCP server exposing Grok (xAI) as a consultation tool for Claude Code."""
import os
import sys

from mcp.server.fastmcp import FastMCP
from openai import OpenAI

XAI_API_KEY = os.environ.get("XAI_API_KEY")
if not XAI_API_KEY:
    print("XAI_API_KEY environment variable is required", file=sys.stderr)
    sys.exit(1)

MODEL = os.environ.get("XAI_MODEL", "grok-4-1-fast-reasoning")

client = OpenAI(api_key=XAI_API_KEY, base_url="https://api.x.ai/v1")
mcp = FastMCP("grok-consultant")


@mcp.tool()
def ask_grok(question: str, context: str = "") -> str:
    """Ask Grok for an independent second opinion.

    Use when you want a perspective from a different model — design decisions,
    debugging dead-ends, "am I missing something?" checks. Grok cannot see this
    conversation, so include the concrete details it needs in `context`.

    Args:
        question: The specific question to ask.
        context: Background Grok needs (code, constraints, what was tried).
    """
    system = (
        "You are Grok, giving a concise second opinion to another AI assistant. "
        "Be direct and specific. Point out things they may have missed. "
        "Disagree when you genuinely disagree. Skip pleasantries."
    )
    user = question if not context else f"Context:\n{context}\n\nQuestion: {question}"
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return resp.choices[0].message.content or ""


@mcp.tool()
def grok_review(code: str, focus: str = "") -> str:
    """Get Grok's review of a code snippet.

    Args:
        code: The code to review.
        focus: Optional focus area (e.g. "security", "performance", "edge cases").
    """
    system = (
        "You are Grok reviewing code for another AI assistant. "
        "Be concrete: name real bugs, edge cases, and design issues. "
        "Skip generic advice and praise."
    )
    user = "Review this code"
    if focus:
        user += f" with focus on: {focus}"
    user += f"\n\n```\n{code}\n```"
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return resp.choices[0].message.content or ""


if __name__ == "__main__":
    mcp.run()
