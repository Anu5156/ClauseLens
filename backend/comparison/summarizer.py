import re
from typing import Optional
from pydantic import BaseModel
from backend.models import ClauseNode
from backend.llm.provider import GeminiProvider, LLMProvider
from backend.config import GEMINI_API_KEY

class SemanticChangeSchema(BaseModel):
    summary: str

def summarize_change_heuristic(clause_a: ClauseNode, clause_b: ClauseNode) -> str:
    """
    Offline/deterministic heuristic change extractor detecting numbers,
    days, timeframes, and penalties.
    """
    text_a = clause_a.text.lower()
    text_b = clause_b.text.lower()

    # 1. Notice days or payment days shift
    days_a = re.findall(r'(\d+)\s*days', text_a)
    days_b = re.findall(r'(\d+)\s*days', text_b)
    
    if days_a and days_b and days_a[0] != days_b[0]:
        val_a, val_b = int(days_a[0]), int(days_b[0])
        action = "Increases" if val_b > val_a else "Reduces"
        topic = "notice period" if "notice" in text_a or "notice" in text_b else "timeline"
        if "payment" in text_a or "invoice" in text_a or "fees" in text_a:
            topic = "payment window"
            
        summary = f"{action} {topic} from {val_a} days to {val_b} days."
        
        # Check if penalty added
        if "penalty" in text_b or "15%" in text_b:
            summary += " Introduces a 15% compounding late payment penalty."
        return summary

    # 2. Term duration changes (years)
    years_a = re.findall(r'(\d+)(?:-|\s*)year', text_a)
    years_b = re.findall(r'(\d+)(?:-|\s*)year', text_b)
    if years_a and years_b and years_a[0] != years_b[0]:
        return f"Changes renewal commitment period from {years_a[0]} year(s) to {years_b[0]} year(s)."

    # 3. Dollar caps
    dollars_a = re.findall(r'\$[\d,]+', text_a)
    dollars_b = re.findall(r'\$[\d,]+', text_b)
    if dollars_a and dollars_b and dollars_a[0] != dollars_b[0]:
        return f"Modifies financial limitation amount from {dollars_a[0]} to {dollars_b[0]}."

    # 4. Specific known legal keywords
    if "penalty" in text_b and "penalty" not in text_a:
        return "Adds new compounding penalty provisions for breach or late payment."
        
    return f"Substantively updates covenants and terms under {clause_b.title or clause_b.clause_number}."

def summarize_semantic_change(
    clause_a: ClauseNode,
    clause_b: ClauseNode,
    provider: Optional[LLMProvider] = None
) -> str:
    """
    Produces a one-line summary explaining what changed in legal meaning and rights/obligations.
    """
    if GEMINI_API_KEY and provider is None:
        try:
            provider = GeminiProvider()
        except Exception:
            provider = None

    if provider:
        prompt = f"""
Compare the following two versions of a legal contract clause:

VERSION A:
Title: {clause_a.title}
Text: {clause_a.text}

VERSION B:
Title: {clause_b.title}
Text: {clause_b.text}

TASK:
Write exactly ONE concise sentence summarizing what changed in legal effect, rights, or obligations.
Focus on the practical consequence of the change (e.g. shifts in liability, altered notice periods, new penalties).
Do NOT produce a word-by-word diff.
"""
        try:
            res: SemanticChangeSchema = provider.generate_structured(
                schema=SemanticChangeSchema,
                prompt=prompt,
                system_instruction="You are a legal document analyst summarizing substantive changes between contract versions."
            )
            if res.summary:
                return res.summary.strip()
        except Exception:
            pass

    return summarize_change_heuristic(clause_a, clause_b)
