from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class SpanLocation(BaseModel):
    page: int
    bbox: List[float] = Field(default_factory=list)  # [x0, y0, x1, y1]
    char_start: int
    char_end: int

class ClauseNode(BaseModel):
    id: str
    document_id: str
    clause_number: str
    title: str
    text: str
    level: int
    category: str = "other"  # Phase 2 Taxonomy category
    parent_id: Optional[str] = None
    children_ids: List[str] = Field(default_factory=list)
    spans: List[SpanLocation] = Field(default_factory=list)
    order_index: int

class CrossRefEdge(BaseModel):
    id: str
    document_id: str
    from_clause_id: str
    from_clause_number: str
    target_label: str
    to_clause_id: Optional[str] = None
    reference_text: str
    is_dangling: bool = False

class DefinedTerm(BaseModel):
    id: str
    document_id: str
    term: str
    definition: str
    clause_id: str

class DefectItem(BaseModel):
    id: str
    document_id: str
    defect_type: str  # e.g. dangling_crossref, undefined_term, conflicting_notice
    description: str
    clause_id: Optional[str] = None
    severity: str = "medium"  # high, medium, low

class DocumentParsed(BaseModel):
    id: str
    filename: str
    file_type: str
    doc_type: str = "unknown"  # Phase 2 document type classification
    upload_timestamp: str
    page_count: int
    raw_text: str
    clauses: List[ClauseNode] = Field(default_factory=list)
    crossrefs: List[CrossRefEdge] = Field(default_factory=list)
    definitions: List[DefinedTerm] = Field(default_factory=list)
    defects: List[DefectItem] = Field(default_factory=list)

class RiskItem(BaseModel):
    id: str
    clause_id: str
    clause_number: str
    category: str
    deviation_rating: str  # standard, aggressive, unusual
    perspective_risk: str  # low, medium, high, critical
    rationale: str
    driving_span: str
    closest_reference_text: str
    closest_reference_type: str

class DocumentRiskProfile(BaseModel):
    document_id: str
    perspective: str
    overall_risk_score: float
    risk_items: List[RiskItem] = Field(default_factory=list)
    inconsistencies: List[DefectItem] = Field(default_factory=list)

class ClauseCitation(BaseModel):
    clause_id: str
    clause_number: str
    title: str
    spans: List[SpanLocation] = Field(default_factory=list)
    snippet: str

class QARequest(BaseModel):
    question: str

class QAResponse(BaseModel):
    question: str
    answer: str
    cited_clauses: List[ClauseCitation] = Field(default_factory=list)
    is_abstention: bool = False
    is_refusal: bool = False
    expanded_context_clause_ids: List[str] = Field(default_factory=list)

class ClauseComparisonItem(BaseModel):
    clause_id_a: Optional[str] = None
    clause_number_a: Optional[str] = None
    title_a: Optional[str] = None
    text_a: Optional[str] = None
    clause_id_b: Optional[str] = None
    clause_number_b: Optional[str] = None
    title_b: Optional[str] = None
    text_b: Optional[str] = None
    category: str = "other"
    status: str  # added, removed, materially_changed, unchanged
    similarity_score: float = 0.0
    semantic_change_summary: Optional[str] = None

class DocumentComparisonResult(BaseModel):
    doc_id_a: str
    doc_id_b: str
    added: List[ClauseComparisonItem] = Field(default_factory=list)
    removed: List[ClauseComparisonItem] = Field(default_factory=list)
    materially_changed: List[ClauseComparisonItem] = Field(default_factory=list)
    unchanged: List[ClauseComparisonItem] = Field(default_factory=list)
    summary_stats: Dict[str, int] = Field(default_factory=dict)

class CompareRequest(BaseModel):
    doc_id_a: str
    doc_id_b: str

class DeadlineItem(BaseModel):
    id: str
    party: str
    obligation: str
    trigger: str
    relative_days: int
    resolved_date: Optional[str] = None
    clause_id: str
    clause_number: str

class DeadlineExport(BaseModel):
    effective_date: str
    deadlines: List[DeadlineItem] = Field(default_factory=list)
    ics_content: str

class LawyerQuestion(BaseModel):
    priority: str  # critical, high, medium
    question: str
    clause_id: str
    clause_number: str
    context_reason: str

class LawyerPrepPack(BaseModel):
    document_id: str
    fact_summary: Dict[str, Any] = Field(default_factory=dict)
    checklist: List[Dict[str, Any]] = Field(default_factory=list)
    prioritized_questions: List[LawyerQuestion] = Field(default_factory=list)

class RewriteRequest(BaseModel):
    level: str = "plain_english"  # plain_english, simple
    language: str = "en"  # en, hi, kn

class RewriteResult(BaseModel):
    level: str
    language: str
    executive_summary: str
    key_rights_summary: str
    clauses_simplified: List[Dict[str, str]] = Field(default_factory=list)

class NegotiationProposal(BaseModel):
    clause_id: str
    clause_number: str
    category: str
    original_text: str
    proposed_alternative_text: str
    one_line_rationale: str



