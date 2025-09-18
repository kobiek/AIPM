"""Product strategy and goal setting for the AI Product Manager."""
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class Objective:
    """Represents a product objective."""
    id: str
    name: str
    description: str
    deadline: datetime
    key_results: List[Dict]
    status: str = "planned"  # planned, in_progress, achieved, failed

class ProductStrategy:
    """Handles product strategy and goal setting."""
    
    def __init__(self, product_name: str, vision: str = ""):
        self.product_name = product_name
        self.vision = vision or f"To be the leading {product_name} in the market"
        self.objectives: Dict[str, Objective] = {}
        self.metrics: Dict[str, Dict] = {}
    
    def set_vision(self, vision: str) -> None:
        """Set or update the product vision."""
        self.vision = vision
    
    def add_objective(
        self, 
        name: str, 
        description: str,
        deadline_days: int = 90,
        key_results: Optional[List[Dict]] = None
    ) -> Objective:
        """Add a new product objective."""
        objective_id = f"obj_{len(self.objectives) + 1}"
        deadline = datetime.now() + timedelta(days=deadline_days)
        
        if key_results is None:
            key_results = [
                {"description": f"Key result 1 for {name}", "target": "100%", "current": "0%"},
                {"description": f"Key result 2 for {name}", "target": "100%", "current": "0%"},
            ]
        
        objective = Objective(
            id=objective_id,
            name=name,
            description=description,
            deadline=deadline,
            key_results=key_results
        )
        
        self.objectives[objective_id] = objective
        return objective
    
    def define_metric(self, name: str, description: str, target: float) -> str:
        """Define a success metric for the product."""
        metric_id = f"metric_{len(self.metrics) + 1}"
        self.metrics[metric_id] = {
            "name": name,
            "description": description,
            "target": target,
            "current": 0.0,
            "unit": "%"  # Default unit, can be overridden
        }
        return metric_id
    
    def update_metric(self, metric_id: str, new_value: float) -> bool:
        """Update the current value of a metric."""
        if metric_id in self.metrics:
            self.metrics[metric_id]["current"] = new_value
            return True
        return False
    
    def get_strategy_summary(self) -> Dict:
        """Get a summary of the product strategy."""
        return {
            "vision": self.vision,
            "objectives_count": len(self.objectives),
            "active_objectives": sum(1 for o in self.objectives.values() if o.status == "in_progress"),
            "metrics": {
                "total": len(self.metrics),
                "on_target": sum(1 for m in self.metrics.values() if m["current"] >= m["target"])
            }
        }
