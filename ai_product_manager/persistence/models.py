"""SQLModel database models."""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class ProductModel(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    description: str
    target_market: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class FeatureModel(SQLModel, table=True):
    id: str = Field(primary_key=True)
    product_id: str = Field(index=True, foreign_key="productmodel.id")
    name: str
    description: str
    status: str = Field(default="backlog")
    priority: int = Field(default=0)
    effort_estimate: Optional[int] = Field(default=None)
    value_score: Optional[int] = Field(default=None)


class ObjectiveModel(SQLModel, table=True):
    id: str = Field(primary_key=True)
    product_id: str = Field(index=True, foreign_key="productmodel.id")
    name: str
    description: str
    deadline: datetime
    status: str = Field(default="planned")


class MetricModel(SQLModel, table=True):
    id: str = Field(primary_key=True)
    product_id: str = Field(index=True, foreign_key="productmodel.id")
    name: str
    description: str
    target: float
    current: float = Field(default=0.0)
    unit: str = Field(default="%")


class SprintModel(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    start_date: datetime
    end_date: datetime
    goal: str
    status: str = Field(default="planned")
    product_id: Optional[str] = Field(default=None, index=True, foreign_key="productmodel.id")


class DecisionLogModel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: str = Field(index=True, foreign_key="productmodel.id")
    timestamp: datetime = Field(default_factory=datetime.now)
    title: str
    details: str
    rationale: str
    alternatives: Optional[str] = None


class HypothesisModel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: str = Field(index=True, foreign_key="productmodel.id")
    description: str
    metric: str
    target: float
    status: str = Field(default="proposed")  # proposed, running, confirmed, rejected
    current: Optional[float] = Field(default=None)
    delta: Optional[float] = Field(default=None)
    evaluated_at: Optional[datetime] = Field(default=None)
    notes: Optional[str] = Field(default=None)


class ResearchItemModel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: str = Field(index=True, foreign_key="productmodel.id")
    source: str  # e.g., hackernews, github, appstore
    title: Optional[str] = Field(default=None)
    url: Optional[str] = Field(default=None, unique=True)
    body: Optional[str] = Field(default=None)
    metadata_json: Optional[str] = Field(default=None)  # JSON-serialized metadata
    created_at: datetime = Field(default_factory=datetime.now)
    tags: Optional[str] = Field(default=None)  # comma-separated tags
    note: Optional[str] = Field(default=None)
    feature_id: Optional[str] = Field(default=None, index=True)  # backlink to FeatureModel.id
    objective_id: Optional[str] = Field(default=None, index=True)  # backlink to ObjectiveModel.id
    processed: bool = Field(default=False, index=True)
