"""AI Product Manager - Main Module"""
import sys
from datetime import datetime, timedelta

from ai_product_manager.core import Product, Feature, AIProductManager
from ai_product_manager.research import MarketResearcher, UserResearcher
from ai_product_manager.strategy import ProductStrategy
from ai_product_manager.planning import RoadmapPlanner
from ai_product_manager.llm import LLMClient
import os
from ai_product_manager.persistence import (
    init_db,
    ProductModel,
    FeatureModel,
    SprintModel,
    ObjectiveModel,
    MetricModel,
    ProductRepository,
    FeatureRepository,
    PlanningRepository,
    StrategyRepository,
)
from ai_product_manager.communication import (
    generate_status_report_md,
    generate_prd_md,
    write_artifact,
)
from ai_product_manager.planning.prioritization import (
    rice_score,
    wsjf_score,
    rank_features,
)
from ai_product_manager.utils.logging import configure_logging
from ai_product_manager.evaluation import propose_hypothesis, evaluate as run_evaluation
from ai_product_manager.research.connectors import fetch_hn, fetch_github_issues, fetch_appstore_reviews
from ai_product_manager.research.synthesis import synthesize

def main():
    """Main entry point for the AI Product Manager."""
    print("🚀 Initializing AI Product Manager...\n")
    configure_logging()
    
    # 0. Init DB
    init_db()

    # 1. Define the product
    product = Product(
        id="pm-ai-001",
        name="AI Product Manager",
        description="An autonomous AI system that performs product management tasks",
        target_market="Startups and product teams looking to automate product management"
    )
    
    # 2. Initialize the AI Product Manager
    pm = AIProductManager(product)
    
    # 3. Set up market research
    print("🔍 Conducting market research...")
    market_researcher = MarketResearcher()
    market_researcher.add_competitor("ProductBoard", "https://www.productboard.com/")
    market_researcher.add_competitor("Aha!", "https://www.aha.io/")
    market_researcher.identify_trends(["AI product management", "autonomous product managers"])
    
    # 4. Set up user research
    print("👥 Analyzing user needs...")
    user_researcher = UserResearcher()
    user_researcher.create_user_persona("Startup Founder", {
        "needs": ["Save time on product management", "Make data-driven decisions"],
        "pain_points": ["Limited resources", "Lack of product expertise"]
    })
    
    # 5. Define product strategy
    print("🎯 Setting product strategy...")
    strategy = ProductStrategy(
        product_name=product.name,
        vision="To empower teams with AI-driven product management capabilities"
    )
    
    # Add objectives
    strategy.add_objective(
        "Launch MVP",
        "Deliver a minimum viable product with core features",
        deadline_days=60
    )
    
    # Define success metrics
    strategy.define_metric("User Engagement", "Daily active users", 1000)
    strategy.define_metric("Feature Usage", "Features used per session", 3)
    
    # 6. Plan the product roadmap
    print("🗺️  Planning product roadmap...")
    planner = RoadmapPlanner(sprint_duration_weeks=2)
    
    # Define some features
    features = [
        {"id": "f1", "name": "User Authentication", "description": "Allow users to sign up and log in", "effort_estimate": 5, "value_score": 8},
        {"id": "f2", "name": "Product Roadmap", "description": "Visualize product roadmap", "effort_estimate": 8, "value_score": 9},
        {"id": "f3", "name": "User Feedback Analysis", "description": "Analyze user feedback using NLP", "effort_estimate": 12, "value_score": 7},
        {"id": "f4", "name": "Competitor Tracking", "description": "Track competitor features and updates", "effort_estimate": 6, "value_score": 6},
        {"id": "f5", "name": "Automated Reporting", "description": "Generate product performance reports", "effort_estimate": 4, "value_score": 7},
    ]
    
    # Add features to the product manager
    for feature_data in features:
        feature = Feature(
            id=feature_data["id"],
            name=feature_data["name"],
            description=feature_data["description"],
            effort_estimate=feature_data["effort_estimate"],
            value_score=feature_data["value_score"]
        )
        pm.add_feature(feature)

    # Persist simple strategy: objectives and metrics
    # Note: using in-memory strategy state created above
    strat_repo = StrategyRepository()
    if strategy.objectives:
        strat_repo.upsert_objectives([
            ObjectiveModel(
                id=o.id,
                product_id=product.id,
                name=o.name,
                description=o.description,
                deadline=o.deadline,
                status=o.status,
            )
            for o in strategy.objectives.values()
        ])
    if strategy.metrics:
        strat_repo.upsert_metrics([
            MetricModel(
                id=k,
                product_id=product.id,
                name=v["name"],
                description=v["description"],
                target=v["target"],
                current=v.get("current", 0.0),
                unit=v.get("unit", "%"),
            )
            for k, v in strategy.metrics.items()
        ])
    
    # Plan the release
    release_plan = planner.plan_release(
        features=features,
        start_date=datetime.now() + timedelta(days=7),  # Start next week
        team_velocity=10  # Story points per sprint
    )
    
    # 7. Persist to DB
    prod_repo = ProductRepository()
    feat_repo = FeatureRepository()
    plan_repo = PlanningRepository()

    prod_repo.create_or_update(
        ProductModel(
            id=product.id,
            name=product.name,
            description=product.description,
            target_market=product.target_market,
        )
    )

    feat_repo.upsert_many(
        [
            FeatureModel(
                id=f["id"],
                product_id=product.id,
                name=f["name"],
                description=f.get("description", ""),
                status="backlog",
                priority=0,
                effort_estimate=f.get("effort_estimate"),
                value_score=f.get("value_score"),
            )
            for f in features
        ]
    )

    if release_plan["sprints"]:
        plan_repo.upsert_sprints(
            [
                SprintModel(
                    id=s.id,
                    name=s.name,
                    start_date=s.start_date,
                    end_date=s.end_date,
                    goal=s.goal,
                    status=s.status,
                    product_id=product.id,
                )
                for s in release_plan["sprints"]
            ]
        )

    # 8. Print the results
    print("\n✅ AI Product Manager Initialized!\n")
    print(f"Product: {product.name}")
    print(f"Vision: {strategy.vision}")
    print(f"Target Market: {product.target_market}")
    
    print("\n📊 Strategy Summary:")
    strategy_summary = strategy.get_strategy_summary()
    print(f"- {strategy_summary['objectives_count']} objectives defined")
    print(f"- {strategy_summary['active_objectives']} active objectives")
    print(f"- {strategy_summary['metrics']['total']} success metrics")
    
    print("\n🚀 Release Plan:")
    if release_plan["sprints"]:
        print(f"Planned release date: {release_plan['estimated_release_date'].strftime('%Y-%m-%d')}")
        print(f"Number of sprints: {len(release_plan['sprints'])}")
        print("\nSprint Plan:")
        for i, sprint in enumerate(release_plan['sprints'], 1):
            print(f"\nSprint {i} ({sprint.start_date.strftime('%b %d')} - {sprint.end_date.strftime('%b %d')}):")
            print(f"Goal: {sprint.goal}")
            print("Features:")
            for fid in sprint.features:
                feature = next(f for f in features if f["id"] == fid)
                print(f"- {feature['name']} ({feature['effort_estimate']} points)")
    else:
        print("No release plan generated. Check your feature list and team velocity.")
    
    print("\n🎉 AI Product Manager is ready to help you build amazing products!")

    # 9. Export artifacts (status report and optional PRD)
    artifacts_dir = os.getenv("AIPM_ARTIFACTS_DIR", os.path.join(os.getcwd(), "artifacts"))
    status_md = generate_status_report_md(
        product={
            "name": product.name,
            "vision": strategy.vision,
            "target_market": product.target_market,
        },
        strategy_summary=strategy_summary,
        release_plan=release_plan,
    )
    status_path = write_artifact(artifacts_dir, f"status_{product.id}.md", status_md)
    print(f"\n📝 Wrote status report to: {status_path}")

    # 9.1 Prioritization rankings (RICE and WSJF)
    rice_ranked = rank_features(features, rice_score)
    wsjf_ranked = rank_features(features, wsjf_score)

    def rankings_md(title: str, ranked):
        lines = [f"# {title}", ""]
        for i, f in enumerate(ranked, 1):
            lines.append(f"{i}. {f['name']} — score: {f['_score']:.3f} (effort={f.get('effort_estimate')}, value={f.get('value_score')})")
        return "\n".join(lines)

    rice_md = rankings_md("RICE Rankings", rice_ranked)
    wsjf_md = rankings_md("WSJF Rankings", wsjf_ranked)
    rice_path = write_artifact(artifacts_dir, f"rankings_rice_{product.id}.md", rice_md)
    wsjf_path = write_artifact(artifacts_dir, f"rankings_wsjf_{product.id}.md", wsjf_md)
    print(f"📝 Wrote prioritization rankings to: {rice_path} and {wsjf_path}")

    # 9.2 Research connectors + synthesis
    print("\n🔎 Fetching external signals (HN + GitHub + App Store) and synthesizing...")
    hn_items = []
    gh_items = []
    as_items = []
    try:
        hn_items = fetch_hn("AI product management", limit=5)
    except Exception:
        pass
    try:
        gh_items = fetch_github_issues("openai/openai-python", query="bug OR feature", limit=5)
    except Exception:
        pass
    try:
        # Example app id (Slack iOS): 618783545 — replace with your app id as needed
        as_items = fetch_appstore_reviews(app_id="618783545", country="us", pages=1, limit=5)
    except Exception:
        pass
    research_items = hn_items + gh_items + as_items
    llm_generate = None
    if os.getenv("GEMINI_API_KEY"):
        try:
            llm = LLMClient()
            llm_generate = llm.generate
        except Exception:
            llm_generate = None
    research_md = synthesize(research_items, llm_generate=llm_generate)
    research_path = write_artifact(artifacts_dir, f"research_synthesis_{product.id}.md", research_md)
    print(f"📝 Wrote research synthesis to: {research_path}")

    # Persist research items to DB
    from ai_product_manager.persistence import ResearchRepository
    ResearchRepository().add_many(product.id, research_items)

    # 10. Evaluation framework: propose a sample hypothesis and evaluate
    hypo = propose_hypothesis(
        product_id=product.id,
        description="Increase Daily Active Users to target",
        metric="User Engagement",
        target=1000,
        notes="Baseline current may be below target in demo run",
    )
    eval_path = run_evaluation(product.id, artifacts_dir=artifacts_dir)
    print(f"📝 Wrote evaluation summary to: {eval_path}")

    # 11. Optional: Draft a PRD using Gemini if API key is set
    if os.getenv("GEMINI_API_KEY"):
        try:
            print("\n🧠 Generating PRD draft with Gemini (optional)...")
            llm = LLMClient()
            # Choose top feature by value/effort
            top_feature = max(
                features,
                key=lambda f: (f.get("value_score", 0)) / (f.get("effort_estimate", 1) or 1)
            )
            # Use first persona created above
            persona = {
                "name": "Startup Founder",
                "needs": ["Save time on product management", "Make data-driven decisions"],
                "pain_points": ["Limited resources", "Lack of product expertise"],
            }
            objectives_list = [
                {"name": o.name, "description": o.description}
                for o in strategy.objectives.values()
            ]
            prd = llm.draft_prd(product.name, top_feature, persona, objectives_list)
            prd_path = write_artifact(
                artifacts_dir,
                f"prd_{product.id}_{top_feature['id']}.md",
                generate_prd_md(product.name, prd, top_feature["name"]),
            )
            print(f"📝 Wrote PRD draft to: {prd_path}")
        except Exception as e:
            print(f"\n[LLM] Skipped PRD generation: {e}")

if __name__ == "__main__":
    main()
