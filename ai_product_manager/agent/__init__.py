"""Agent loop for weekly planning and retros."""
from datetime import datetime, timedelta
import os
from typing import List, Dict, Optional

from ai_product_manager.persistence import (
    init_db,
    ProductRepository,
    FeatureRepository,
    PlanningRepository,
    DecisionLogRepository,
    DecisionLogModel,
    ResearchRepository,
)
from ai_product_manager.planning.prioritization import rank_features, rice_score
from ai_product_manager.communication import (
    write_artifact,
    generate_status_report_md,
)
from ai_product_manager.research.synthesis import synthesize
from ai_product_manager.llm import LLMClient
from ai_product_manager.evaluation import propose_hypothesis
from ai_product_manager.utils.config import load_agent_config


def _predict_week_capacity() -> int:
    # Simple heuristic; later read from past velocity
    return 10


def _draft_weekly_plan(product, features: List[Dict]) -> str:
    ranked = rank_features(features, rice_score)
    capacity = _predict_week_capacity()
    selected = []
    remaining = capacity
    for f in ranked:
        effort = int(f.get("effort_estimate") or 1)
        if effort <= remaining:
            selected.append(f)
            remaining -= effort
    lines = [
        f"# Weekly Plan for {product.name}",
        "",
        f"Week of: {datetime.now():%Y-%m-%d}",
        f"Capacity: {capacity} pts",
        "",
        "## Planned Features",
    ]
    if selected:
        for f in selected:
            lines.append(f"- {f['name']} ({f.get('effort_estimate')} pts) — RICE {f['_score']:.2f}")
    else:
        lines.append("- No features selected")
    return "\n".join(lines)


def _draft_retro() -> str:
    lines = [
        f"# Retro Notes",
        "",
        "What went well:",
        "- Placeholder",
        "",
        "What can be improved:",
        "- Placeholder",
        "",
        "Actions:",
        "- Placeholder",
    ]
    return "\n".join(lines)


def run_weekly_cycle(artifacts_dir: Optional[str] = None) -> Dict[str, str]:
    init_db()
    cfg = load_agent_config()
    prod_repo = ProductRepository()
    feat_repo = FeatureRepository()
    dec_repo = DecisionLogRepository()
    research_repo = ResearchRepository()

    products = prod_repo.list()
    if not products:
        raise RuntimeError("No products found. Run the main CLI once to seed data.")
    product = products[0]

    feature_models = feat_repo.list_by_product(product.id)
    features = [
        {
            "id": f.id,
            "name": f.name,
            "description": f.description,
            "effort_estimate": f.effort_estimate,
            "value_score": f.value_score,
        }
        for f in feature_models
    ]

    plan_md = _draft_weekly_plan(product, features)
    retro_md = _draft_retro()

    out_dir = artifacts_dir or os.path.join(os.getcwd(), "artifacts")
    plan_path = write_artifact(out_dir, f"weekly_plan_{product.id}.md", plan_md)
    retro_path = write_artifact(out_dir, f"retro_{product.id}.md", retro_md)

    dec_repo.add(
        DecisionLogModel(
            product_id=product.id,
            title="Weekly plan drafted",
            details=f"Artifacts: {plan_path}, {retro_path}",
            rationale="RICE-based selection under capacity heuristic",
        )
    )

    # Insights: synthesize from recent research items
    research_items = research_repo.list_by_product(product.id)
    # Convert to dicts
    rlimit = int(cfg.get("research", {}).get("limit", 20))
    items_dicts = [
        {"source": ri.source, "title": ri.title, "url": ri.url, "body": ri.body}
        for ri in research_items[-rlimit:]
    ]
    llm_generate = None
    try:
        llm = LLMClient()
        llm_generate = llm.generate
    except Exception:
        llm_generate = None
    insights_md = synthesize(items_dicts, llm_generate=llm_generate)
    insights_path = write_artifact(out_dir, f"insights_weekly_{product.id}.md", insights_md)

    # Propose a simple hypothesis from insights context
    try:
        metric = str(cfg.get("hypothesis", {}).get("metric", "User Engagement"))
        target = float(cfg.get("hypothesis", {}).get("target", 1000))
        propose_hypothesis(
            product_id=product.id,
            description=f"Increase {metric} via top weekly insight",
            metric=metric,
            target=target,
            notes="Auto-proposed by weekly agent",
        )
    except Exception:
        pass

    dec_repo.add(
        DecisionLogModel(
            product_id=product.id,
            title="Weekly insights synthesized",
            details=f"Artifacts: {insights_path}",
            rationale="Summarized recent research items",
        )
    )

    return {"plan": plan_path, "retro": retro_path, "insights": insights_path}


def main():
    """CLI entrypoint to run a single weekly cycle."""
    try:
        result = run_weekly_cycle()
        print("✅ Weekly cycle complete")
        print(f"Plan:  {result['plan']}")
        print(f"Retro: {result['retro']}")
        if 'insights' in result and result['insights']:
            print(f"Insights: {result['insights']}")
    except Exception as e:
        print(f"[Agent] Error: {e}")
