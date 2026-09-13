import re
from typing import List, Optional, Tuple, Dict, Any
from pydantic import BaseModel, Field
from backend.config import GEMINI_API_KEY, RETRIEVAL_CONFIDENCE_THRESHOLD
from backend.models import DocumentParsed, ClauseNode, ClauseCitation, QAResponse
from backend.qa.retriever import hybrid_retrieve_clauses, tokenize
from backend.qa.context_expander import expand_clause_context
from backend.llm.provider import GeminiProvider, LLMProvider

LEGAL_ADVICE_TRIGGERS = [
    r'\b(what should i do|what do you advise|should i sign|should i accept)\b',
    r'\b(will i win|can i sue|chances in court|outcome of litigation)\b',
    r'\b(how to breach|how can i get out of|how to avoid paying)\b',
    r'\b(is it safe to|would you recommend)\b'
]

class GroundedAnswerSchema(BaseModel):
    answer: str
    cited_clause_ids: List[str] = Field(default_factory=list)
    is_abstention: bool = False

STOPWORDS = {
    "what", "is", "the", "does", "any", "how", "are", "for", "with", "this", "that",
    "and", "or", "in", "on", "at", "by", "from", "to", "of", "a", "an", "as", "be",
    "if", "do", "can", "will", "would", "should", "it", "its", "their", "there", "about",
    "under", "into", "over", "such", "than", "then", "so"
}

def check_refusal_legal_advice(question: str) -> bool:
    q_lower = question.lower()
    for pattern in LEGAL_ADVICE_TRIGGERS:
        if re.search(pattern, q_lower):
            return True
    return False

def answer_question(
    doc: DocumentParsed,
    question: str,
    provider: Optional[LLMProvider] = None
) -> QAResponse:
    """
    Executes grounded Question-Answering over doc with:
    1. Legal advice refusal detection
    2. Hybrid retrieval (BM25 + Dense)
    3. Context expansion (parents, crossrefs, definitions)
    4. Abstention if query not in document
    5. Structured citation generation with bounding box spans
    """
    is_refusal = check_refusal_legal_advice(question)

    # Check for Abstention on Out-of-Scope query using lexical ground truth
    q_tokens = tokenize(question)
    meaningful_q_tokens = [t for t in q_tokens if t not in STOPWORDS]
    
    doc_text_lower = doc.raw_text.lower()
    matches_found = [t for t in meaningful_q_tokens if t in doc_text_lower]
    
    # If key subject terms do not exist in the document, abstain
    if meaningful_q_tokens and (len(matches_found) == 0 or len(matches_found) / len(meaningful_q_tokens) < 0.3):
        return QAResponse(
            question=question,
            answer=f"This document does not contain information regarding '{question}'. No matching provisions, rules, or defined terms exist in the contract text.",
            cited_clauses=[],
            is_abstention=True,
            is_refusal=is_refusal,
            expanded_context_clause_ids=[]
        )

    # 1. Retrieve Candidate Clauses
    retrieved = hybrid_retrieve_clauses(question, doc.clauses, top_k=4)
    if not retrieved:
        return QAResponse(
            question=question,
            answer=f"This document does not contain information regarding your query.",
            cited_clauses=[],
            is_abstention=True,
            is_refusal=is_refusal,
            expanded_context_clause_ids=[]
        )

    # 2. Expand Context
    candidate_clauses = [c for c, _ in retrieved if _ > 0.005][:3]
    if not candidate_clauses and retrieved:
        candidate_clauses = [retrieved[0][0]]

    expanded = expand_clause_context(candidate_clauses, doc)
    
    # Build citation objects for primary and expanded clauses
    clause_lookup: Dict[str, ClauseNode] = {c.id: c for c in doc.clauses}
    cited_citations: List[ClauseCitation] = []
    
    for c in candidate_clauses:
        snippet = c.text[:120] + "..." if len(c.text) > 120 else c.text
        cited_citations.append(ClauseCitation(
            clause_id=c.id,
            clause_number=c.clause_number,
            title=c.title,
            spans=c.spans,
            snippet=snippet
        ))

    # 3. Generate Answer (LLM or Heuristic Extractive Fallback)
    if GEMINI_API_KEY and provider is None:
        try:
            provider = GeminiProvider()
        except Exception:
            provider = None

    answer_text = ""
    if provider:
        context_str = "\n\n".join([
            f"[Clause ID: {c.id}] Clause {c.clause_number} - {c.title}:\n{c.text}"
            for c in candidate_clauses + expanded["parent_clauses"] + expanded["crossref_clauses"]
        ])
        if expanded["definitions"]:
            context_str += "\n\n[Applicable Definitions]:\n" + "\n".join([
                f"- \"{d.term}\": {d.definition}" for d in expanded["definitions"]
            ])

        prompt = f"""
QUESTION: {question}

DOCUMENT CONTEXT:
{context_str}

CRITICAL RULES:
1. Provide a factual, objective answer strictly based on the provided clauses.
2. Cite the exact Clause IDs supporting your statements.
3. If the answer is not contained in the text, set is_abstention=True and clearly state that the contract does not address it.
4. NEVER provide legal advice or predict outcomes.
"""
        try:
            res: GroundedAnswerSchema = provider.generate_structured(
                schema=GroundedAnswerSchema,
                prompt=prompt,
                system_instruction="You are a legal document retrieval assistant providing factual clause explanations with citations."
            )
            answer_text = res.answer
            if res.is_abstention:
                return QAResponse(
                    question=question,
                    answer=res.answer,
                    cited_clauses=[],
                    is_abstention=True,
                    is_refusal=is_refusal,
                    expanded_context_clause_ids=expanded["all_expanded_ids"]
                )
        except Exception:
            provider = None  # fall through to offline extractive synthesis

    if not answer_text:
        # Offline Extractive Synthesis
        primary = candidate_clauses[0]
        answer_text = f"According to Clause {primary.clause_number} ({primary.title}): \"{primary.text.strip()}\""
        if len(candidate_clauses) > 1:
            sec = candidate_clauses[1]
            answer_text += f"\n\nAdditionally, Clause {sec.clause_number} ({sec.title}) provides: \"{sec.text.strip()}\""

    # Append Refusal Guardrail Disclaimer if legal advice was solicited
    if is_refusal:
        answer_text += (
            "\n\n[NOTICE - Legal Advice Refusal]: You asked for legal recommendations or outcome assessments. "
            "ClauseLens operates strictly as an objective analytical tool and does not provide legal advice or recommend actions. "
            "The excerpts above reflect the factual terms in the contract. Please consult a qualified legal professional to evaluate strategy or litigation risks."
        )

    return QAResponse(
        question=question,
        answer=answer_text,
        cited_clauses=cited_citations,
        is_abstention=False,
        is_refusal=is_refusal,
        expanded_context_clause_ids=expanded["all_expanded_ids"]
    )
