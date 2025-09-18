import os
import uuid
from datetime import datetime
import streamlit as st

from ai_product_manager.persistence import (
    init_db,
    ProductRepository,
    FeatureRepository,
    PlanningRepository,
    ResearchRepository,
    FeatureModel,
    ObjectiveModel,
    StrategyRepository,
)
from ai_product_manager.planning.prioritization import rank_features, rice_score, wsjf_score
from ai_product_manager.communication import (
    generate_status_report_md,
    generate_prd_md,
    write_artifact,
)
from ai_product_manager.llm import LLMClient
from ai_product_manager.research.connectors import (
    fetch_hn,
    fetch_github_issues,
    fetch_appstore_reviews,
    fetch_zendesk_tickets,
    fetch_intercom_conversations,
    fetch_serpapi_news,
    fetch_google_news_rss,
)
from ai_product_manager.research.synthesis import synthesize
from ai_product_manager.evaluation import propose_hypothesis


def load_data():
    prod_repo = ProductRepository()
    feat_repo = FeatureRepository()
    plan_repo = PlanningRepository()
    research_repo = ResearchRepository()

    products = prod_repo.list()
    product = products[0] if products else None
    features = feat_repo.list_by_product(product.id) if product else []
    research_items = research_repo.list_by_product(product.id) if product else []
    sprints = plan_repo.upsert_sprints([]) if False else []  # placeholder to import model

    return product, features, research_items


def main():
    st.set_page_config(page_title="AI Product Manager", layout="wide")
    st.title("AI Product Manager Dashboard")

    init_db()
    product, features, research_items = load_data()

    if not product:
        st.warning("No product found in DB. Run the CLI first: `python3 -m ai_product_manager`. ")
        return

    st.subheader("Product")
    col1, col2, col3 = st.columns(3)
    col1.metric("Product ID", product.id)
    col2.metric("Name", product.name)
    col3.metric("Target Market", product.target_market)

    st.divider()

    st.subheader("Features")
    if features:
        st.dataframe(
            [{
                "id": f.id,
                "name": f.name,
                "status": f.status,
                "priority": f.priority,
                "effort": f.effort_estimate,
                "value": f.value_score,
            } for f in features],
            use_container_width=True,
        )
    else:
        st.info("No features saved for this product yet.")

    st.divider()

    st.subheader("Prioritization")
    features_dicts = [
        {
            "id": f.id,
            "name": f.name,
            "effort_estimate": f.effort_estimate,
            "value_score": f.value_score,
        }
        for f in features
    ]
    rice = rank_features(features_dicts, rice_score)
    wsjf = rank_features(features_dicts, wsjf_score)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### RICE Rankings")
        for i, f in enumerate(rice, 1):
            st.write(f"{i}. {f['name']} — score: {f['_score']:.3f} (effort={f.get('effort_estimate')}, value={f.get('value_score')})")
    with col2:
        st.markdown("### WSJF Rankings")
        for i, f in enumerate(wsjf, 1):
            st.write(f"{i}. {f['name']} — score: {f['_score']:.3f} (effort={f.get('effort_estimate')}, value={f.get('value_score')})")

    st.divider()

    st.subheader("Artifacts")
    artifacts_dir = os.getenv("AIPM_ARTIFACTS_DIR", os.path.join(os.getcwd(), "artifacts"))

    colA, colB = st.columns(2)
    with colA:
        if st.button("Generate Status Report"):
            strategy_summary = {"objectives_count": 1, "active_objectives": 0, "metrics": {"total": 2, "on_target": 0}}
            status_md = generate_status_report_md(
                product={"name": product.name, "vision": "", "target_market": product.target_market},
                strategy_summary=strategy_summary,
                release_plan={"sprints": [], "estimated_release_date": None},
            )
            path = write_artifact(artifacts_dir, f"status_{product.id}.md", status_md)
            st.success(f"Status report saved: {path}")

    with colB:
        if st.button("Generate PRD (Gemini)"):
            try:
                llm = LLMClient()
                if not features_dicts:
                    st.warning("No features available for PRD generation.")
                else:
                    top_feature = max(features_dicts, key=lambda f: (f.get("value_score", 0)) / (f.get("effort_estimate", 1) or 1))
                    persona = {"name": "Startup Founder", "needs": ["Save time"], "pain_points": ["Limited resources"]}
                    prd = llm.draft_prd(product.name, top_feature, persona, [])
                    path = write_artifact(artifacts_dir, f"prd_{product.id}_{top_feature['id']}.md", generate_prd_md(product.name, prd, top_feature["name"]))
                    st.success(f"PRD saved: {path}")
            except Exception as e:
                st.warning(f"LLM unavailable or error: {e}")

    st.caption("Set GEMINI_API_KEY in your environment for PRD generation.")

    st.divider()
    st.subheader("Research")
    # Filters
    sources = sorted({ri.source for ri in research_items}) if research_items else []
    sel_sources = st.multiselect("Filter by source", options=sources, default=sources)
    hide_processed = st.checkbox("Hide processed", value=True)
    filtered = [
        ri for ri in research_items
        if (not sel_sources or ri.source in sel_sources) and (not hide_processed or not ri.processed)
    ]

    if filtered:
        st.write(f"Showing {len(filtered)} items")
        st.dataframe([
            {
                "id": ri.id,
                "source": ri.source,
                "title": ri.title,
                "url": ri.url,
                "snippet": (ri.body or "")[:120],
            }
            for ri in filtered
        ], use_container_width=True)
    else:
        st.info("No research items yet. Use the fetchers below or run the CLI main.")

    # Selection for summarization / bulk actions
    selected_ids = st.multiselect(
        "Select items to summarize",
        options=[ri.id for ri in filtered],
        format_func=lambda _id: next((ri.title or f"{ri.source}:{ri.id}" for ri in filtered if ri.id == _id), str(_id)),
    )

    if selected_ids and st.button("Mark Selected as Processed"):
        repo = ResearchRepository()
        updated = 0
        for rid in selected_ids:
            try:
                if repo.mark_processed(int(rid)):
                    updated += 1
            except Exception:
                pass
        st.success(f"Marked {updated} items as processed")

    colx, coly, colz = st.columns(3)
    with colx:
        hn_query = st.text_input("HN query", value="AI product management")
        if st.button("Fetch HN"):
            try:
                items = fetch_hn(hn_query, limit=10)
                count = ResearchRepository().add_many(product.id, items)
                st.success(f"Fetched and saved {count} HN items")
            except Exception as e:
                st.warning(f"HN fetch failed: {e}")
    with coly:
        gh_repo = st.text_input("GitHub repo", value="openai/openai-python")
        gh_q = st.text_input("GitHub query", value="bug OR feature")
        if st.button("Fetch GitHub"):
            try:
                items = fetch_github_issues(gh_repo, query=gh_q, limit=10)
                count = ResearchRepository().add_many(product.id, items)
                st.success(f"Fetched and saved {count} GitHub issues")
            except Exception as e:
                st.warning(f"GitHub fetch failed: {e}")
    with colz:
        app_id = st.text_input("App Store App ID", value="618783545")
        if st.button("Fetch App Store"):
            try:
                items = fetch_appstore_reviews(app_id=app_id, country="us", pages=1, limit=10)
                count = ResearchRepository().add_many(product.id, items)
                st.success(f"Fetched and saved {count} App Store reviews")
            except Exception as e:
                st.warning(f"App Store fetch failed: {e}")

    st.markdown("### News")
    coln1, coln2 = st.columns(2)
    with coln1:
        st.markdown("#### SerpAPI News")
        news_q = st.text_input("News query", value="AI product management")
        date_from = st.text_input("After (YYYY-MM-DD)", value="")
        date_to = st.text_input("Before (YYYY-MM-DD)", value="")
        if st.button("Fetch SerpAPI News"):
            try:
                items = fetch_serpapi_news(news_q, num=10, date_from=(date_from or None), date_to=(date_to or None))
                count = ResearchRepository().add_many(product.id, items)
                st.success(f"Fetched and saved {count} news items (SerpAPI)")
            except Exception as e:
                st.warning(f"SerpAPI news fetch failed: {e}")
    with coln2:
        st.markdown("#### Google News RSS")
        rss_q = st.text_input("RSS query", value="AI product management")
        if st.button("Fetch RSS News"):
            try:
                items = fetch_google_news_rss(rss_q, num=10)
                count = ResearchRepository().add_many(product.id, items)
                st.success(f"Fetched and saved {count} news items (RSS)")
            except Exception as e:
                st.warning(f"RSS news fetch failed: {e}")

    st.markdown("### Support Tickets")
    colz1, colz2 = st.columns(2)
    with colz1:
        st.markdown("#### Zendesk")
        zd_sub = st.text_input("Zendesk subdomain", value=os.getenv("ZENDESK_SUBDOMAIN", ""))
        zd_email = st.text_input("Zendesk email", value=os.getenv("ZENDESK_EMAIL", ""))
        zd_token = st.text_input("Zendesk API token", type="password", value=os.getenv("ZENDESK_API_TOKEN", ""))
        zd_query = st.text_input("Zendesk query", value="type:ticket status<solved")
        if st.button("Fetch Zendesk"):
            if not (zd_sub and zd_email and zd_token):
                st.warning("Please provide subdomain, email, and API token.")
            else:
                try:
                    items = fetch_zendesk_tickets(zd_sub, zd_email, zd_token, query=zd_query, limit=20)
                    count = ResearchRepository().add_many(product.id, items)
                    st.success(f"Fetched and saved {count} Zendesk tickets")
                except Exception as e:
                    st.warning(f"Zendesk fetch failed: {e}")
    with colz2:
        st.markdown("#### Intercom")
        ic_token = st.text_input("Intercom Access Token", type="password", value=os.getenv("INTERCOM_ACCESS_TOKEN", ""))
        ic_state = st.selectbox("State", options=["open", "closed"], index=0)
        if st.button("Fetch Intercom"):
            if not ic_token:
                st.warning("Please provide Intercom access token.")
            else:
                try:
                    items = fetch_intercom_conversations(ic_token, state=ic_state, limit=20)
                    count = ResearchRepository().add_many(product.id, items)
                    st.success(f"Fetched and saved {count} Intercom conversations")
                except Exception as e:
                    st.warning(f"Intercom fetch failed: {e}")

    # Summarize selected
    if st.button("Summarize Selected"):
        try:
            selected = [ri for ri in filtered if ri.id in selected_ids]
            items_dicts = [
                {"source": ri.source, "title": ri.title, "url": ri.url, "body": ri.body}
                for ri in selected
            ]
            llm_generate = None
            try:
                llm = LLMClient()
                llm_generate = llm.generate
            except Exception:
                llm_generate = None
            synthesis = synthesize(items_dicts, llm_generate=llm_generate)
            artifacts_dir = os.getenv("AIPM_ARTIFACTS_DIR", os.path.join(os.getcwd(), "artifacts"))
            path = write_artifact(artifacts_dir, f"research_synthesis_{product.id}_selected.md", synthesis)
            st.success(f"Synthesis saved: {path}")
        except Exception as e:
            st.warning(f"Summarization failed: {e}")

    # Extract Insights from selected
    st.markdown("### Extract Insights")
    default_metric = st.text_input("Metric name for hypotheses", value="User Engagement")
    default_target = st.number_input("Target value", value=1000, step=100)
    create_hypos = st.checkbox("Also propose hypotheses from insights", value=False)
    if st.button("Extract Insights from Selected"):
        try:
            selected = [ri for ri in filtered if ri.id in selected_ids]
            if not selected:
                st.info("Select at least one item above.")
            else:
                items_dicts = [
                    {"source": ri.source, "title": ri.title, "url": ri.url, "body": ri.body}
                    for ri in selected
                ]
                # Build an insights-oriented prompt if LLM is available
                insights_md = None
                try:
                    llm = LLMClient()
                    prompt = (
                        "You are a Staff PM. From the following research items, extract 3-7 actionable insights as bullet points. "
                        "Each insight should be concise (<= 25 words) and include a short rationale. Then propose up to 3 hypotheses of the form: "
                        "'If we X, then metric Y will change from A to B'. End with a brief 'Opportunities' section.\n\n"
                    )
                    for i, it in enumerate(items_dicts, 1):
                        prompt += f"[{i}] {it.get('source')}: {it.get('title')} — {it.get('url')}\n"
                        body = (it.get("body") or "")[:500]
                        if body:
                            prompt += f"Snippet: {body}\n"
                    prompt += "\nReturn Markdown with sections: Insights, Hypotheses, Opportunities."
                    insights_md = llm.generate(prompt)
                except Exception:
                    # Fallback: simple list of titles as 'insights'
                    insights_md = "# Insights\n\n" + "\n".join(f"- {it.get('title') or '(untitled)'}" for it in items_dicts)

                artifacts_dir = os.getenv("AIPM_ARTIFACTS_DIR", os.path.join(os.getcwd(), "artifacts"))
                path = write_artifact(artifacts_dir, f"insights_{product.id}_selected.md", insights_md)
                st.success(f"Insights saved: {path}")

                if create_hypos:
                    # Create 1-3 sample hypotheses using default metric/target
                    try:
                        # Just propose one example hypothesis for now
                        propose_hypothesis(
                            product_id=product.id,
                            description=f"Improve {default_metric} via top insight",
                            metric=default_metric,
                            target=float(default_target),
                            notes="Auto-proposed from Insights action",
                        )
                        st.success("Proposed a hypothesis based on insights.")
                    except Exception as e:
                        st.warning(f"Failed to propose hypothesis: {e}")
        except Exception as e:
            st.warning(f"Insights extraction failed: {e}")

    st.markdown("### Research Item Detail")
    if filtered:
        editable_id = st.selectbox(
            "Choose an item to edit",
            options=[ri.id for ri in filtered],
            format_func=lambda _id: next((ri.title or f"{ri.source}:{ri.id}" for ri in filtered if ri.id == _id), str(_id)),
        )
        if editable_id is not None:
            repo = ResearchRepository()
            row = repo.get(int(editable_id))
            if row:
                st.write(f"Source: {row.source}")
                st.write(f"URL: {row.url or '(none)'}")
                st.text_area("Body (read-only)", value=row.body or "", height=150, disabled=True)
                tags_val = st.text_input("Tags (comma-separated)", value=row.tags or "")
                note_val = st.text_area("Note", value=row.note or "", height=120)
                if st.button("Save Changes"):
                    try:
                        updated = repo.update_tags_note(int(editable_id), tags=tags_val.strip() or None, note=note_val.strip() or None)
                        if updated:
                            st.success("Saved. Reloading...")
                            st.rerun()
                        else:
                            st.warning("Item not found; refresh and try again.")
                    except Exception as e:
                        st.warning(f"Save failed: {e}")

                st.checkbox("Processed", value=bool(row.processed), disabled=True)
                if not row.processed and st.button("Mark Processed"):
                    try:
                        repo.mark_processed(int(editable_id), True)
                        st.success("Item marked as processed. Reloading...")
                        st.rerun()
                    except Exception as e:
                        st.warning(f"Failed to mark processed: {e}")

                st.markdown("#### Create Feature from this Insight")
                default_name = (row.title or "New Feature from Insight")[:80]
                feat_name = st.text_input("Feature name", value=default_name, key=f"feat_name_{editable_id}")
                feat_desc = st.text_area("Feature description", value=(row.body or row.title or "")[:500], height=120, key=f"feat_desc_{editable_id}")
                colf1, colf2 = st.columns(2)
                with colf1:
                    feat_effort = st.number_input("Effort estimate (story points)", min_value=1, max_value=100, value=5, step=1, key=f"feat_eff_{editable_id}")
                with colf2:
                    feat_value = st.number_input("Value score (1-10)", min_value=1, max_value=10, value=8, step=1, key=f"feat_val_{editable_id}")
                if st.button("Create Feature from Insight"):
                    try:
                        fid = f"f_{uuid.uuid4().hex[:8]}"
                        # Persist feature
                        FeatureRepository().upsert_many([
                            FeatureModel(
                                id=fid,
                                product_id=product.id,
                                name=feat_name.strip() or default_name,
                                description=feat_desc.strip() or default_name,
                                status="backlog",
                                priority=0,
                                effort_estimate=int(feat_effort),
                                value_score=int(feat_value),
                            )
                        ])
                        # Link back to research item
                        repo.link_feature(int(editable_id), fid)
                        st.success(f"Feature created: {fid} and linked to this insight.")
                    except Exception as e:
                        st.warning(f"Feature creation failed: {e}")

                st.markdown("#### Create Objective from this Insight")
                obj_name = st.text_input("Objective name", value=(row.title or "New Objective from Insight")[:80], key=f"obj_name_{editable_id}")
                obj_desc = st.text_area("Objective description", value=(row.body or row.title or "")[:500], height=120, key=f"obj_desc_{editable_id}")
                obj_deadline_days = st.number_input("Deadline in days", min_value=7, max_value=365, value=60, step=1, key=f"obj_deadline_{editable_id}")
                if st.button("Create Objective from Insight"):
                    try:
                        oid = f"o_{uuid.uuid4().hex[:8]}"
                        deadline = datetime.now() + timedelta(days=int(obj_deadline_days))
                        StrategyRepository().upsert_objectives([
                            ObjectiveModel(
                                id=oid,
                                product_id=product.id,
                                name=obj_name.strip() or (row.title or "Objective"),
                                description=obj_desc.strip() or (row.body or ""),
                                deadline=deadline,
                                status="proposed",
                            )
                        ])
                        repo.link_objective(int(editable_id), oid)
                        st.success(f"Objective created: {oid} and linked to this insight.")
                    except Exception as e:
                        st.warning(f"Objective creation failed: {e}")


if __name__ == "__main__":
    main()
