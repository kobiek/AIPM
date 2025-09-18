"""Repository classes for persistence operations."""
from typing import List, Optional, Iterable
from sqlmodel import select
from .db import get_session
from .models import (
    ProductModel,
    FeatureModel,
    ObjectiveModel,
    MetricModel,
    SprintModel,
    DecisionLogModel,
    HypothesisModel,
    ResearchItemModel,
)


class ProductRepository:
    def create_or_update(self, product: ProductModel) -> ProductModel:
        with get_session() as session:
            existing = session.get(ProductModel, product.id)
            if existing:
                for field in ["name", "description", "target_market", "created_at", "updated_at"]:
                    setattr(existing, field, getattr(product, field))
                session.add(existing)
                session.commit()
                session.refresh(existing)
                return existing
            session.add(product)
            session.commit()
            session.refresh(product)
            return product

    def get(self, product_id: str) -> Optional[ProductModel]:
        with get_session() as session:
            return session.get(ProductModel, product_id)

    def list(self) -> List[ProductModel]:
        with get_session() as session:
            return list(session.exec(select(ProductModel)))


class FeatureRepository:
    def upsert_many(self, features: Iterable[FeatureModel]) -> List[FeatureModel]:
        saved = []
        with get_session() as session:
            for f in features:
                existing = session.get(FeatureModel, f.id)
                if existing:
                    for field in ["product_id", "name", "description", "status", "priority", "effort_estimate", "value_score"]:
                        setattr(existing, field, getattr(f, field))
                    session.add(existing)
                    session.flush()
                    saved.append(existing)
                else:
                    session.add(f)
                    session.flush()
                    saved.append(f)
            session.commit()
        return saved

    def list_by_product(self, product_id: str) -> List[FeatureModel]:
        with get_session() as session:
            return list(session.exec(select(FeatureModel).where(FeatureModel.product_id == product_id)))


class ResearchRepository:
    def add_many(self, product_id: str, items: Iterable[dict]) -> int:
        """Insert research items, ignoring duplicates by URL."""
        inserted = 0
        with get_session() as session:
            for it in items:
                url = it.get("url")
                # Skip if URL already exists
                if url:
                    existing = list(session.exec(select(ResearchItemModel).where(ResearchItemModel.url == url)))
                    if existing:
                        continue
                row = ResearchItemModel(
                    product_id=product_id,
                    source=it.get("source", "unknown"),
                    title=it.get("title"),
                    url=it.get("url"),
                    body=it.get("body"),
                    metadata_json=str(it.get("metadata")) if it.get("metadata") is not None else None,
                )
                session.add(row)
                inserted += 1
            session.commit()
        return inserted

    def list_by_product(self, product_id: str) -> List[ResearchItemModel]:
        with get_session() as session:
            return list(session.exec(select(ResearchItemModel).where(ResearchItemModel.product_id == product_id)))

    def list_unprocessed_by_product(self, product_id: str, limit: int = 20) -> List[ResearchItemModel]:
        with get_session() as session:
            q = select(ResearchItemModel).where(
                (ResearchItemModel.product_id == product_id) & (ResearchItemModel.processed == False)  # noqa: E712
            )
            items = list(session.exec(q))
            return items[:limit]

    def get(self, item_id: int) -> Optional[ResearchItemModel]:
        with get_session() as session:
            return session.get(ResearchItemModel, item_id)

    def update_tags_note(self, item_id: int, tags: Optional[str], note: Optional[str]) -> Optional[ResearchItemModel]:
        with get_session() as session:
            row = session.get(ResearchItemModel, item_id)
            if not row:
                return None
            row.tags = tags
            row.note = note
            session.add(row)
            session.commit()
            session.refresh(row)
            return row

    def link_feature(self, item_id: int, feature_id: str) -> Optional[ResearchItemModel]:
        with get_session() as session:
            row = session.get(ResearchItemModel, item_id)
            if not row:
                return None
            row.feature_id = feature_id
            session.add(row)
            session.commit()
            session.refresh(row)
            return row

    def link_objective(self, item_id: int, objective_id: str) -> Optional[ResearchItemModel]:
        with get_session() as session:
            row = session.get(ResearchItemModel, item_id)
            if not row:
                return None
            row.objective_id = objective_id
            session.add(row)
            session.commit()
            session.refresh(row)
            return row

    def mark_processed(self, item_id: int, processed: bool = True) -> Optional[ResearchItemModel]:
        with get_session() as session:
            row = session.get(ResearchItemModel, item_id)
            if not row:
                return None
            row.processed = processed
            session.add(row)
            session.commit()
            session.refresh(row)
            return row


class DecisionLogRepository:
    def add(self, entry: DecisionLogModel) -> DecisionLogModel:
        with get_session() as session:
            session.add(entry)
            session.commit()
            session.refresh(entry)
            return entry

    def list_for_product(self, product_id: str) -> List[DecisionLogModel]:
        with get_session() as session:
            return list(session.exec(select(DecisionLogModel).where(DecisionLogModel.product_id == product_id)))


class HypothesisRepository:
    def add(self, h: HypothesisModel) -> HypothesisModel:
        with get_session() as session:
            session.add(h)
            session.commit()
            session.refresh(h)
            return h

    def list_for_product(self, product_id: str) -> List[HypothesisModel]:
        with get_session() as session:
            return list(session.exec(select(HypothesisModel).where(HypothesisModel.product_id == product_id)))

    def update(self, h: HypothesisModel) -> HypothesisModel:
        with get_session() as session:
            existing = session.get(HypothesisModel, h.id)
            if not existing:
                raise ValueError("Hypothesis not found")
            for field in [
                "product_id",
                "description",
                "metric",
                "target",
                "status",
                "current",
                "delta",
                "evaluated_at",
                "notes",
            ]:
                setattr(existing, field, getattr(h, field))
            session.add(existing)
            session.commit()
            session.refresh(existing)
            return existing


class StrategyRepository:
    def upsert_objectives(self, objectives: Iterable[ObjectiveModel]) -> List[ObjectiveModel]:
        saved = []
        with get_session() as session:
            for o in objectives:
                existing = session.get(ObjectiveModel, o.id)
                if existing:
                    for field in ["product_id", "name", "description", "deadline", "status"]:
                        setattr(existing, field, getattr(o, field))
                    session.add(existing)
                    session.flush()
                    saved.append(existing)
                else:
                    session.add(o)
                    session.flush()
                    saved.append(o)
            session.commit()
        return saved

    def upsert_metrics(self, metrics: Iterable[MetricModel]) -> List[MetricModel]:
        saved = []
        with get_session() as session:
            for m in metrics:
                existing = session.get(MetricModel, m.id)
                if existing:
                    for field in ["product_id", "name", "description", "target", "current", "unit"]:
                        setattr(existing, field, getattr(m, field))
                    session.add(existing)
                    session.flush()
                    saved.append(existing)
                else:
                    session.add(m)
                    session.flush()
                    saved.append(m)
            session.commit()
        return saved

    def list_metrics_by_product(self, product_id: str) -> List[MetricModel]:
        with get_session() as session:
            return list(session.exec(select(MetricModel).where(MetricModel.product_id == product_id)))


class PlanningRepository:
    def upsert_sprints(self, sprints: Iterable[SprintModel]) -> List[SprintModel]:
        saved = []
        with get_session() as session:
            for s in sprints:
                existing = session.get(SprintModel, s.id)
                if existing:
                    for field in ["name", "start_date", "end_date", "goal", "status", "product_id"]:
                        setattr(existing, field, getattr(s, field))
                    session.add(existing)
                    session.flush()
                    saved.append(existing)
                else:
                    session.add(s)
                    session.flush()
                    saved.append(s)
            session.commit()
        return saved
