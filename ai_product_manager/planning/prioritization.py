"""Prioritization frameworks: RICE and WSJF.

All functions accept a feature dict with optional fields.
If fields are missing, sensible defaults are used so the functions remain usable.

Expected optional fields:
- RICE: reach (users per time), impact (0.25..3.0), confidence (0..1), effort_estimate (story points)
- WSJF: business_value, time_criticality, risk_reduction, job_size (or effort_estimate)
"""
from typing import Dict, List


def rice_score(f: Dict) -> float:
    reach = float(f.get("reach", 1))
    impact = float(f.get("impact", max(0.25, min(3.0, (f.get("value_score", 5) or 5) / 3.33))))  # map value_score 1-10 -> ~0.3-3
    confidence = float(f.get("confidence", 0.8))
    effort = float(f.get("effort_estimate", 1) or 1)
    return (reach * impact * confidence) / effort


def wsjf_score(f: Dict) -> float:
    business_value = float(f.get("business_value", f.get("value_score", 5) or 5))
    time_criticality = float(f.get("time_criticality", 1))
    risk_reduction = float(f.get("risk_reduction", 1))
    job_size = float(f.get("job_size", f.get("effort_estimate", 1) or 1))
    return (business_value + time_criticality + risk_reduction) / job_size


def rank_features(features: List[Dict], scorer) -> List[Dict]:
    scored = []
    for f in features:
        try:
            score = float(scorer(f))
        except Exception:
            score = 0.0
        scored.append({**f, "_score": score})
    return sorted(scored, key=lambda x: x["_score"], reverse=True)
