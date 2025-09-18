"""Evaluation framework for hypotheses and simple A/B style outcomes.

This module allows proposing hypotheses tied to a metric, then evaluating them
based on current metric values. It generates a Markdown summary artifact.
"""
from __future__ import annotations
from datetime import datetime
import os
from typing import Optional, List, Dict

from ai_product_manager.persistence import (
    init_db,
    StrategyRepository,
    HypothesisRepository,
    HypothesisModel,
    ProductRepository,
)
from ai_product_manager.communication import write_artifact


def propose_hypothesis(product_id: str, description: str, metric: str, target: float, notes: Optional[str] = None) -> HypothesisModel:
    init_db()
    hrepo = HypothesisRepository()
    h = HypothesisModel(
        product_id=product_id,
        description=description,
        metric=metric,
        target=target,
        status="proposed",
        notes=notes,
    )
    return hrepo.add(h)


ess_status_map = {
    "confirmed": "✅ Confirmed",
    "rejected": "❌ Rejected",
    "running": "🟡 Running",
    "proposed": "📝 Proposed",
}


def evaluate(product_id: str, artifacts_dir: Optional[str] = None) -> str:
    """Evaluate all hypotheses for a product against current metrics.

    - If metric current >= target -> confirmed.
    - Else if current is present but < target -> rejected.
    - Else -> running.
    Writes a Markdown summary and returns the artifact path.
    """
    init_db()
    srepo = StrategyRepository()
    hrepo = HypothesisRepository()

    metrics = {m.name: m for m in srepo.list_metrics_by_product(product_id)}
    hypos = hrepo.list_for_product(product_id)

    lines = [f"# Evaluation Summary for {product_id}", "", f"Date: {datetime.now():%Y-%m-%d}", ""]

    if not hypos:
        lines.append("No hypotheses to evaluate.")
    else:
        for h in hypos:
            m = metrics.get(h.metric)
            if m is None:
                h.status = "running"
                h.current = None
                h.delta = None
                h.evaluated_at = datetime.now()
            else:
                current = float(m.current)
                target = float(h.target)
                h.current = current
                h.delta = current - target
                h.evaluated_at = datetime.now()
                h.status = "confirmed" if current >= target else "rejected"
            hrepo.update(h)
            status_emoji = ess_status_map.get(h.status, h.status)
            lines.append(f"## {status_emoji} {h.description}")
            lines.append(f"- Metric: {h.metric}")
            if h.current is not None:
                lines.append(f"- Current: {h.current}")
                lines.append(f"- Target: {h.target}")
                lines.append(f"- Delta: {h.delta}")
            else:
                lines.append("- Current: n/a (metric not found)")
            if h.notes:
                lines.append(f"- Notes: {h.notes}")
            lines.append("")

    out_dir = artifacts_dir or os.path.join(os.getcwd(), "artifacts")
    path = write_artifact(out_dir, f"evaluation_{product_id}.md", "\n".join(lines))
    return path
