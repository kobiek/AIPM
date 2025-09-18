"""Core module for the AI Product Manager system."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime

@dataclass
class Product:
    """Represents a product managed by the AI Product Manager."""
    id: str
    name: str
    description: str
    target_market: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class Feature:
    """Represents a product feature."""
    id: str
    name: str
    description: str
    status: str = "backlog"  # backlog, planned, in_progress, completed
    priority: int = 0
    effort_estimate: Optional[int] = None  # in story points or days
    value_score: Optional[int] = None  # 1-10 scale

class AIProductManager:
    """Main class for the AI Product Manager system."""
    
    def __init__(self, product: Product):
        self.product = product
        self.features: Dict[str, Feature] = {}
        self.market_insights: Dict = {}
        self.roadmap: Dict = {}
        
    def add_feature(self, feature: Feature) -> None:
        """Add a new feature to the product."""
        self.features[feature.id] = feature
        self._update_roadmap()
    
    def prioritize_features(self) -> List[Feature]:
        """Prioritize features based on value and effort."""
        return sorted(
            self.features.values(),
            key=lambda f: (
                f.priority,
                (f.value_score or 0) / (f.effort_estimate or 1)
            ),
            reverse=True
        )
    
    def _update_roadmap(self) -> None:
        """Update the product roadmap based on current features and priorities."""
        # This is a simplified version - in a real implementation, this would be more sophisticated
        planned = [f for f in self.features.values() if f.status == "planned"]
        backlog_or_planned = [f for f in self.features.values() if f.status in ["backlog", "planned"]]
        self.roadmap = {
            "now": [f for f in self.features.values() if f.status == "in_progress"],
            "next": planned[:3],
            "later": backlog_or_planned[3:]
        }
    
    def generate_status_report(self) -> str:
        """Generate a status report on the product."""
        return f"""
        Product: {self.product.name}
        Description: {self.product.description}
        
        Features:
        {len([f for f in self.features.values() if f.status == 'completed'])} completed
        {len([f for f in self.features.values() if f.status == 'in_progress'])} in progress
        {len([f for f in self.features.values() if f.status in ['backlog', 'planned']])} in backlog
        
        Top Priority Features:
        {chr(10).join(f'- {f.name} (Priority: {f.priority})' for f in self.prioritize_features()[:3])}
        """
