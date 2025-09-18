"""Communication module for generating stakeholder artifacts (Markdown)."""
from datetime import datetime
from typing import Dict, List, Any
import os


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def sanitize_filename(name: str) -> str:
    # Allow dot to preserve extensions
    return "".join(c for c in name if c.isalnum() or c in ("-", "_", " ", ".")).rstrip().replace(" ", "_")


def generate_status_report_md(product: Dict[str, Any], strategy_summary: Dict[str, Any], release_plan: Dict[str, Any]) -> str:
    lines = []
    lines.append(f"# Status Report - {product['name']}")
    lines.append("")
    lines.append(f"Date: {datetime.now():%Y-%m-%d}")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Product: {product['name']}")
    lines.append(f"- Vision: {product.get('vision', '')}")
    lines.append(f"- Target Market: {product.get('target_market', '')}")
    lines.append("")
    lines.append("## Strategy")
    lines.append(f"- Objectives: {strategy_summary['objectives_count']}")
    lines.append(f"- Active Objectives: {strategy_summary['active_objectives']}")
    lines.append(f"- Metrics Tracked: {strategy_summary['metrics']['total']}")
    lines.append(f"- Metrics On Target: {strategy_summary['metrics']['on_target']}")
    lines.append("")
    lines.append("## Release Plan")
    if release_plan.get("sprints"):
        lines.append(f"- Planned release date: {release_plan['estimated_release_date']:%Y-%m-%d}")
        lines.append(f"- Number of sprints: {len(release_plan['sprints'])}")
        lines.append("")
        for i, s in enumerate(release_plan["sprints"], 1):
            lines.append(f"### Sprint {i}: {s.name} ({s.start_date:%b %d} - {s.end_date:%b %d})")
            lines.append(f"- Goal: {s.goal}")
            lines.append("")
    else:
        lines.append("- No sprints planned yet.")
    return "\n".join(lines)


def generate_prd_md(product_name: str, prd_text: str, feature_name: str) -> str:
    header = f"# PRD: {feature_name} (Product: {product_name})\n\nGenerated: {datetime.now():%Y-%m-%d %H:%M}\n\n---\n\n"
    return header + (prd_text or "[Empty PRD]")


def write_artifact(output_dir: str, filename: str, content: str) -> str:
    ensure_dir(output_dir)
    path = os.path.join(output_dir, sanitize_filename(filename))
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path
