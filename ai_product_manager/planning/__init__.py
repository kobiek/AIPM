"""Product planning and roadmap management for the AI Product Manager."""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import random

@dataclass
class Sprint:
    """Represents a development sprint."""
    id: str
    name: str
    start_date: datetime
    end_date: datetime
    goal: str
    features: List[str]  # List of feature IDs
    status: str = "planned"  # planned, in_progress, completed

class RoadmapPlanner:
    """Handles product roadmap planning and sprint management."""
    
    def __init__(self, sprint_duration_weeks: int = 2):
        self.sprint_duration = sprint_duration_weeks
        self.sprints: Dict[str, Sprint] = {}
        self.feature_backlog: List[Dict] = []
        self.velocity = 10  # Default story points per sprint
    
    def create_sprint_plan(
        self, 
        name: str, 
        start_date: datetime, 
        features: List[Dict],
        goal: str = ""
    ) -> Sprint:
        """Create a new sprint plan."""
        sprint_id = f"sprint_{len(self.sprints) + 1}"
        end_date = start_date + timedelta(weeks=self.sprint_duration)
        
        sprint = Sprint(
            id=sprint_id,
            name=name,
            start_date=start_date,
            end_date=end_date,
            goal=goal or f"Deliver {len(features)} features",
            features=[f["id"] for f in features]
        )
        
        self.sprints[sprint_id] = sprint
        return sprint
    
    def plan_release(
        self, 
        features: List[Dict], 
        start_date: datetime = None,
        target_release_date: datetime = None,
        team_velocity: int = None
    ) -> Dict:
        """Plan a product release with the given features."""
        if not features:
            return {"sprints": [], "estimated_release_date": None}
            
        if start_date is None:
            start_date = datetime.now()
            
        velocity = team_velocity or self.velocity
        
        # Sort features by priority (highest first)
        sorted_features = sorted(
            features, 
            key=lambda x: (x.get("priority", 0), x.get("value_score", 0)), 
            reverse=True
        )
        
        sprints = []
        current_sprint_start = start_date
        remaining_features = sorted_features.copy()
        
        while remaining_features:
            # Calculate sprint end date
            sprint_end = current_sprint_start + timedelta(weeks=self.sprint_duration)
            
            # Check if we have a target release date and this sprint would exceed it
            if target_release_date and sprint_end > target_release_date:
                break
            
            # Select features for this sprint based on velocity
            sprint_capacity = velocity
            sprint_features = []
            
            while remaining_features and sprint_capacity > 0:
                feature = remaining_features[0]
                feature_effort = feature.get("effort_estimate", 1)
                
                if feature_effort <= sprint_capacity:
                    sprint_features.append(remaining_features.pop(0))
                    sprint_capacity -= feature_effort
                else:
                    # If the next feature is too big for remaining capacity, try to find a smaller one
                    for i, f in enumerate(remaining_features[1:], 1):
                        if f.get("effort_estimate", 1) <= sprint_capacity:
                            sprint_features.append(remaining_features.pop(i))
                            sprint_capacity -= f.get("effort_estimate", 1)
                            break
                    else:
                        # No smaller feature found, break the loop
                        break

            # If no features could be scheduled in this sprint, break to avoid infinite loop
            if not sprint_features:
                # Could not fit any feature into the sprint capacity; stop planning
                break
            
            # Create sprint
            sprint_name = f"Sprint {len(sprints) + 1}"
            sprint = self.create_sprint_plan(
                name=sprint_name,
                start_date=current_sprint_start,
                features=sprint_features,
                goal=f"Complete {len(sprint_features)} features"
            )
            
            sprints.append(sprint)
            current_sprint_start = sprint_end
            
            # If we've reached the target release date, stop planning
            if target_release_date and sprint_end >= target_release_date:
                break
        
        estimated_release_date = sprints[-1].end_date if sprints else None
        
        return {
            "sprints": sprints,
            "estimated_release_date": estimated_release_date,
            "remaining_features": remaining_features
        }
    
    def calculate_feature_priority(
        self, 
        value_score: float, 
        effort_estimate: float, 
        strategic_alignment: float = 1.0,
        risk_factor: float = 1.0
    ) -> float:
        """
        Calculate priority score for a feature.
        Higher score means higher priority.
        """
        if effort_estimate <= 0:
            effort_estimate = 1  # Avoid division by zero
            
        # Simple formula: value / effort, adjusted by strategic alignment and risk
        priority = (value_score * strategic_alignment) / (effort_estimate * risk_factor)
        return priority
