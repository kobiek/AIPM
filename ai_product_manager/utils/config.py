"""Configuration utilities for AI Product Manager.
Reads settings from environment variables with sensible defaults.
Also supports loading agent-specific configuration from a YAML file.
"""
import os
from dataclasses import dataclass
from typing import Optional, Dict, Any

try:
    import yaml  # type: ignore
except Exception:
    yaml = None  # optional dependency; YAML loading will gracefully degrade


@dataclass
class Settings:
    db_path: str
    artifacts_dir: str
    gemini_api_key: Optional[str]
    gemini_model: str


def load_settings() -> Settings:
    cwd = os.getcwd()
    return Settings(
        db_path=os.getenv("AIPM_DB_PATH", os.path.join(cwd, "aipm.db")),
        artifacts_dir=os.getenv("AIPM_ARTIFACTS_DIR", os.path.join(cwd, "artifacts")),
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
    )


def load_agent_config() -> Dict[str, Any]:
    """Load agent configuration from YAML file and environment overrides.

    Lookup order:
    - AIPM_AGENT_CONFIG env var (path to YAML)
    - ./agent_config.yaml (CWD)
    - ai_product_manager/agent_config.yaml (package default)

    Supported keys (with defaults):
    - hypothesis.metric: "User Engagement"
    - hypothesis.target: 1000
    - research.limit: 20
    - research.slice: "recent"  # reserved for future: recent, unprocessed
    Env overrides:
    - AIPM_AGENT_METRIC
    - AIPM_AGENT_TARGET
    - AIPM_AGENT_RESEARCH_LIMIT
    """
    defaults = {
        "hypothesis": {"metric": "User Engagement", "target": 1000},
        "research": {"limit": 20, "slice": "recent"},
    }

    # Load YAML if available
    cfg: Dict[str, Any] = {}
    yaml_path: Optional[str] = os.getenv("AIPM_AGENT_CONFIG")
    search_paths = [
        yaml_path,
        os.path.join(os.getcwd(), "agent_config.yaml"),
        os.path.join(os.path.dirname(__file__), "..", "agent_config.yaml"),
    ]
    for p in search_paths:
        if p and os.path.isfile(p) and yaml is not None:
            try:
                with open(p, "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f) or {}
                break
            except Exception:
                pass

    # Merge defaults
    result = defaults
    # Shallow merge for known sections
    if isinstance(cfg, dict):
        if isinstance(cfg.get("hypothesis"), dict):
            result["hypothesis"].update(cfg["hypothesis"])  # type: ignore
        if isinstance(cfg.get("research"), dict):
            result["research"].update(cfg["research"])  # type: ignore

    # Env overrides
    metric = os.getenv("AIPM_AGENT_METRIC")
    if metric:
        result["hypothesis"]["metric"] = metric
    target = os.getenv("AIPM_AGENT_TARGET")
    if target:
        try:
            result["hypothesis"]["target"] = float(target)
        except ValueError:
            pass
    rlim = os.getenv("AIPM_AGENT_RESEARCH_LIMIT")
    if rlim:
        try:
            result["research"]["limit"] = int(rlim)
        except ValueError:
            pass

    return result
