"""LLM integration using Google Gemini."""
import os
from typing import Optional, Dict, Any, List

try:
    import google.generativeai as genai
except ImportError as e:
    genai = None  # Will raise at runtime if used without package installed


class LLMClient:
    """Wrapper for Google Gemini text generation."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not set. Provide api_key or set the GEMINI_API_KEY environment variable."
            )
        if genai is None:
            raise RuntimeError(
                "google-generativeai is not installed. Please install it with 'pip install google-generativeai'."
            )
        genai.configure(api_key=self.api_key)
        self.model_name = model
        self._model = genai.GenerativeModel(model)

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from a prompt."""
        resp = self._model.generate_content(prompt, **kwargs)
        # Handle both string and parts
        text = getattr(resp, "text", None)
        if not text and hasattr(resp, "candidates") and resp.candidates:
            # Fallback concatenate parts
            parts = []
            for cand in resp.candidates:
                for part in getattr(cand, "content", {}).get("parts", []):
                    parts.append(str(part))
            text = "\n".join(parts)
        return (text or "").strip()

    def draft_prd(self, product_name: str, feature: Dict[str, Any], persona: Dict[str, Any], objectives: List[Dict[str, Any]]) -> str:
        """Draft a concise PRD for a feature."""
        prompt = f"""
        You are a senior product manager. Draft a concise PRD (<= 400 words) for the feature described below.
        Include: Problem, Goals/Success Metrics, Scope (What/Not), Risks, and Milestones.
        
        Product: {product_name}
        Feature: {feature.get('name')}
        Description: {feature.get('description')}
        Effort estimate: {feature.get('effort_estimate')} pts
        Value score: {feature.get('value_score')}
        
        Primary persona: {persona.get('name')}
        Persona needs: {', '.join(persona.get('needs', []))}
        Persona pain points: {', '.join(persona.get('pain_points', []))}
        
        Current objectives:
        {chr(10).join('- ' + o.get('name', o.get('description', '')) for o in objectives)}
        
        Write in crisp, executive-ready language.
        """
        return self.generate(prompt)
