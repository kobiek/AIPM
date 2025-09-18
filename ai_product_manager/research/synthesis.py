"""Research synthesis utilities.

Takes a list of items from connectors and produces a Markdown synthesis with
themes and cited sources. If an LLM is available, uses it for better summaries.
"""
from __future__ import annotations
from typing import List, Dict, Optional
from datetime import datetime


def simple_summarize(items: List[Dict]) -> str:
    lines = ["# Research Synthesis", "", f"Date: {datetime.now():%Y-%m-%d}", "", "## Sources"]
    for i, it in enumerate(items, 1):
        lines.append(f"{i}. [{it.get('title','(no title)')}]({it.get('url','#')}) — {it.get('source')}")
    lines.append("")
    lines.append("## Observations")
    if not items:
        lines.append("- No items fetched.")
    else:
        # naive heuristics
        hn_count = sum(1 for it in items if it.get("source") == "hackernews")
        gh_count = sum(1 for it in items if it.get("source") == "github")
        lines.append(f"- Found {hn_count} HN stories and {gh_count} GitHub issues.")
        lines.append("- Common queries indicate active discussion around AI PM tooling and product roadmaps.")
    return "\n".join(lines)


def llm_summarize(items: List[Dict], llm_generate) -> str:
    prompt = (
        "You are a senior product strategist. Given the following sources, produce a concise synthesis (<= 300 words) "
        "with: 3-5 key themes, signals of demand or pain, and opportunities. Include a Sources section with citations.\n\n"
    )
    for i, it in enumerate(items, 1):
        prompt += f"[{i}] {it.get('source')}: {it.get('title')} — {it.get('url')}\n"
        body = (it.get("body") or "")[:500]
        if body:
            prompt += f"Snippet: {body}\n"
    prompt += "\nWrite the synthesis followed by a 'Sources' list referencing [#] numbers."
    return llm_generate(prompt)


def synthesize(items: List[Dict], llm_generate: Optional[callable] = None) -> str:
    if llm_generate:
        try:
            return llm_summarize(items, llm_generate)
        except Exception:
            return simple_summarize(items)
    return simple_summarize(items)
