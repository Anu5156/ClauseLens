"""
Unit tests for ClauseLens Pydantic models.
Run with:  pytest tests/test_models.py -v
"""
import pytest
from backend.models import (
    SpanLocation, ClauseNode, CrossRefEdge, DefinedTerm,
    DefectItem, DocumentParsed, RiskItem, DocumentRiskProfile,
    ClauseCitation, QARequest, QAResponse,
    ClauseComparisonItem, DocumentComparisonResult, CompareRequest,
    DeadlineItem, DeadlineExport, LawyerQuestion, LawyerPrepPack,
    RewriteRequest, RewriteResult, NegotiationProposal,
)


# ─── SpanLocation ─────────────────────────────────────────────────────────────

class TestSpanLocation:
    def test_valid_span(self):
        s = SpanLocation(page=1, bbox=[0.0, 0.0, 100.0, 20.0], char_start=0, char_end=50)
        assert s.page == 1
        assert len(s.bbox) == 4

    def test_bbox_defaults_to_empty_list(self):
        s = SpanLocation(page=0, char_start=0, char_end=0)
        assert s.bbox == []


# ─── ClauseNode ───────────────────────────────────────────────────────────────

class TestClauseNode:
    def _make(self, **kwargs):
        defaults = dict(
            id="c1", document_id="d1", clause_number="1",
            title="Payment", text="Vendor shall pay...", level=1, order_index=0,
        )
        defaults.update(kwargs)
        return ClauseNode(**defaults)

    def test_defaults(self):
        c = self._make()
        assert c.category == "other"
        assert c.parent_id is None
        assert c.children_ids == []
        assert c.spans == []

    def test_custom_category(self):
        c = self._make(category="payment")
        assert c.category == "payment"

    def test_children_ids_independent(self):
        c1 = self._make()
        c2 = self._make(id="c2")
        c1.children_ids.append("child-x")
        assert c2.children_ids == [], "Default list must not be shared between instances"


# ─── CrossRefEdge ─────────────────────────────────────────────────────────────

class TestCrossRefEdge:
    def test_not_dangling_by_default(self):
        e = CrossRefEdge(
            id="r1", document_id="d1", from_clause_id="c1",
            from_clause_number="1.1", target_label="2", reference_text="See Section 2",
        )
        assert e.is_dangling is False
        assert e.to_clause_id is None

    def test_dangling_flag(self):
        e = CrossRefEdge(
            id="r2", document_id="d1", from_clause_id="c1",
            from_clause_number="1.1", target_label="99", reference_text="See §99",
            is_dangling=True,
        )
        assert e.is_dangling is True


# ─── DefinedTerm ──────────────────────────────────────────────────────────────

class TestDefinedTerm:
    def test_all_fields_required(self):
        dt = DefinedTerm(
            id="def1", document_id="d1",
            term="Confidential Information",
            definition="Any non-public data disclosed under this Agreement.",
            clause_id="c3",
        )
        assert dt.term == "Confidential Information"


# ─── DefectItem ───────────────────────────────────────────────────────────────

class TestDefectItem:
    def test_severity_default(self):
        d = DefectItem(
            id="def1", document_id="d1",
            defect_type="dangling_crossref", description="Ref to §99 missing",
        )
        assert d.severity == "medium"
        assert d.clause_id is None


# ─── DocumentParsed ───────────────────────────────────────────────────────────

class TestDocumentParsed:
    def _base(self):
        return DocumentParsed(
            id="d1", filename="contract.pdf", file_type="pdf",
            upload_timestamp="2025-01-01T00:00:00Z",
            page_count=10, raw_text="The contract...",
        )

    def test_doc_type_default(self):
        doc = self._base()
        assert doc.doc_type == "unknown"

    def test_lists_default_empty(self):
        doc = self._base()
        assert doc.clauses == []
        assert doc.crossrefs == []
        assert doc.definitions == []
        assert doc.defects == []

    def test_with_clauses(self):
        clause = ClauseNode(
            id="c1", document_id="d1", clause_number="1",
            title="Scope", text="...", level=1, order_index=0,
        )
        doc = self._base()
        doc.clauses.append(clause)
        assert len(doc.clauses) == 1


# ─── RiskItem ─────────────────────────────────────────────────────────────────

class TestRiskItem:
    def test_fields(self):
        ri = RiskItem(
            id="ri1", clause_id="c1", clause_number="4.1",
            category="liability", deviation_rating="aggressive",
            perspective_risk="high", rationale="One-sided cap.",
            driving_span="Vendor not liable", closest_reference_text="Market standard",
            closest_reference_type="industry",
        )
        assert ri.deviation_rating == "aggressive"
        assert ri.perspective_risk == "high"


# ─── DocumentRiskProfile ──────────────────────────────────────────────────────

class TestDocumentRiskProfile:
    def test_defaults(self):
        drp = DocumentRiskProfile(
            document_id="d1", perspective="tenant",
            overall_risk_score=7.2,
        )
        assert drp.risk_items == []
        assert drp.inconsistencies == []


# ─── QA Models ────────────────────────────────────────────────────────────────

class TestQAModels:
    def test_qa_request(self):
        r = QARequest(question="What is the termination clause?")
        assert r.question == "What is the termination clause?"

    def test_qa_response_defaults(self):
        r = QAResponse(question="q", answer="a")
        assert r.cited_clauses == []
        assert r.is_abstention is False
        assert r.is_refusal is False
        assert r.expanded_context_clause_ids == []

    def test_clause_citation(self):
        cc = ClauseCitation(
            clause_id="c1", clause_number="3.2",
            title="IP Rights", snippet="All IP belongs to...",
        )
        assert cc.spans == []


# ─── Comparison Models ────────────────────────────────────────────────────────

class TestComparisonModels:
    def test_compare_request(self):
        r = CompareRequest(doc_id_a="d1", doc_id_b="d2")
        assert r.doc_id_a == "d1"

    def test_result_defaults(self):
        r = DocumentComparisonResult(doc_id_a="d1", doc_id_b="d2")
        assert r.added == []
        assert r.removed == []
        assert r.materially_changed == []
        assert r.unchanged == []
        assert r.summary_stats == {}

    def test_clause_item_defaults(self):
        item = ClauseComparisonItem(status="added")
        assert item.status == "added"
        assert item.similarity_score == 0.0
        assert item.semantic_change_summary is None

    def test_clause_item_all_statuses(self):
        for status in ("added", "removed", "materially_changed", "unchanged"):
            item = ClauseComparisonItem(status=status)
            assert item.status == status


# ─── Deadline Models ──────────────────────────────────────────────────────────

class TestDeadlineModels:
    def test_deadline_item(self):
        dl = DeadlineItem(
            id="dl1", party="Customer", obligation="Notify vendor",
            trigger="30 days before renewal", relative_days=30,
            clause_id="c1", clause_number="12.2",
        )
        assert dl.relative_days == 30
        assert dl.resolved_date is None

    def test_deadline_export(self):
        dl = DeadlineItem(
            id="dl1", party="Customer", obligation="Notify vendor",
            trigger="30 days before renewal", relative_days=30,
            clause_id="c1", clause_number="12.2",
        )
        export = DeadlineExport(
            effective_date="2025-01-01", deadlines=[dl], ics_content="BEGIN:VCALENDAR",
        )
        assert len(export.deadlines) == 1
        assert export.effective_date == "2025-01-01"


# ─── LawyerPrepPack ───────────────────────────────────────────────────────────

class TestLawyerPrepPack:
    def test_defaults(self):
        pack = LawyerPrepPack(document_id="d1")
        assert pack.fact_summary == {}
        assert pack.checklist == []
        assert pack.prioritized_questions == []

    def test_lawyer_question(self):
        q = LawyerQuestion(
            priority="critical", question="Is indemnity mutual?",
            clause_id="c5", clause_number="8.1",
            context_reason="One-sided indemnity detected",
        )
        assert q.priority == "critical"


# ─── Rewrite Models ───────────────────────────────────────────────────────────

class TestRewriteModels:
    def test_request_defaults(self):
        req = RewriteRequest()
        assert req.level == "plain_english"
        assert req.language == "en"

    def test_result_defaults(self):
        r = RewriteResult(
            level="plain_english", language="en",
            executive_summary="Short summary.",
            key_rights_summary="Your rights are...",
        )
        assert r.clauses_simplified == []


# ─── NegotiationProposal ──────────────────────────────────────────────────────

class TestNegotiationProposal:
    def test_all_fields(self):
        np_ = NegotiationProposal(
            clause_id="c2", clause_number="4.3", category="liability",
            original_text="Vendor not liable for any consequential damages.",
            proposed_alternative_text="Vendor liability capped at 3× annual fees.",
            one_line_rationale="Removes unlimited liability exposure for Customer.",
        )
        assert np_.proposed_alternative_text.startswith("Vendor liability")
        assert np_.one_line_rationale
