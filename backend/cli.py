import sys
import argparse
from pathlib import Path

# Ensure UTF-8 output encoding for multilingual text (Hindi, Kannada) on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
from backend.sample_generator import create_all_samples
from backend.ingestion.pipeline import ingest_document
from backend.ingestion.classifier import classify_and_profile_document
from backend.ingestion.risk_analyzer import analyze_document_risk
from backend.qa.engine import answer_question
from backend.comparison.aligner import compare_documents
from backend.actionable.deadlines import extract_deadlines
from backend.actionable.lawyer_prep import build_lawyer_prep_pack
from backend.actionable.rewriter import generate_document_rewrite
from backend.actionable.negotiation import generate_negotiation_proposals

def print_clause_tree(clauses):
    print("\n" + "="*80)
    print(" [TREE] CLAUSE TREE HIERARCHY")
    print("="*80)
    for c in clauses:
        indent = "  " * (c.level - 1)
        parent_info = f" (parent: {c.parent_id})" if c.parent_id else " (root)"
        category_tag = f" [{c.category.upper()}]" if hasattr(c, "category") and c.category != "other" else ""
        bbox_info = f" [p.{c.spans[0].page} bbox={c.spans[0].bbox}]" if c.spans else ""
        print(f"{indent}+-- [{c.clause_number}] {c.title}{category_tag}{parent_info}{bbox_info}")
        snippet = c.text.replace("\n", " ")[:90]
        if len(c.text) > 90:
            snippet += "..."
        print(f"{indent}|   +-- Text: \"{snippet}\"")

def print_crossrefs(crossrefs):
    print("\n" + "="*80)
    print(" [CROSSREFS] CROSS-REFERENCE GRAPH EDGES")
    print("="*80)
    if not crossrefs:
        print("  (No cross-references detected)")
        return
    for ref in crossrefs:
        status = "DANGLING [MISSING TARGET]" if ref.is_dangling else f"RESOLVED -> {ref.to_clause_id}"
        print(f"  * Clause {ref.from_clause_number} -> Ref: '{ref.target_label}' [{status}]")

def print_defects(defects):
    print("\n" + "="*80)
    print(" [DEFECTS] DETECTED DOCUMENT FLAWS & DEFECTS")
    print("="*80)
    if not defects:
        print("  (No defects detected)")
        return
    for d in defects:
        clause_str = f" [Clause ID: {d.clause_id}]" if d.clause_id else ""
        print(f"  * [{d.severity.upper()}] {d.defect_type.upper()}: {d.description}{clause_str}")

def print_profile(profile):
    print("\n" + "="*80)
    print(" [PROFILE] DOCUMENT PROFILE & MISSING CLAUSE ANALYSIS")
    print("="*80)
    print(f"  * Document Type: {profile.doc_type_name} ({profile.doc_type})")
    print(f"  * Total Clauses: {profile.total_clauses}")
    print("\n  [TAXONOMY COUNTS] Clause-Type Distribution:")
    non_zero_counts = {k: v for k, v in profile.clause_type_counts.items() if v > 0}
    for cat, count in non_zero_counts.items():
        print(f"    - {cat}: {count}")

    print("\n  [PRESENT] Expected Clauses Found:")
    for exp in profile.present_clauses:
        print(f"    + {exp}")

    print("\n  [MISSING CLAUSES] Headline Absent Feature Report:")
    if not profile.missing_clauses:
        print("    (No missing clauses detected - document has complete standard coverage)")
    else:
        for missing in profile.missing_clauses:
            print(f"    - [ABSENT] {missing}")

def print_risk_profile(risk_profile):
    print("\n" + "="*80)
    print(f" [RISK PANEL] PERSPECTIVE RISK EVALUATION ({risk_profile.perspective.upper()})")
    print("="*80)
    print(f"  * Overall Perspective Risk Score: {risk_profile.overall_risk_score}/100")
    print(f"  * Total Risk Items Assessed: {len(risk_profile.risk_items)}")
    print(f"  * Total Inconsistencies/Flaws Caught: {len(risk_profile.inconsistencies)}")
    print("\n  [CLAUSE DEVIATION ASSESSMENT & SIDE-BY-SIDE BENCHMARK]")
    for item in risk_profile.risk_items:
        severity_tag = f"[{item.perspective_risk.upper()}]"
        deviation_tag = f"[{item.deviation_rating.upper()} DEVIATION]"
        print(f"\n  + Clause {item.clause_number} ({item.category.upper()}) {severity_tag} {deviation_tag}")
        print(f"    - Rationale: {item.rationale}")
        print(f"    - Driving Key Span: \"{item.driving_span}\"")
        if item.closest_reference_text:
            ref_snippet = item.closest_reference_text[:110] + "..." if len(item.closest_reference_text) > 110 else item.closest_reference_text
            print(f"    - Side-by-Side Market Reference ({item.closest_reference_type}):")
            print(f"      \"{ref_snippet}\"")

    print("\n  [DETERMINISTIC INCONSISTENCY & FLAW AUDIT]")
    if not risk_profile.inconsistencies:
        print("  (No deterministic inconsistencies or flaws detected)")
    else:
        for inc in risk_profile.inconsistencies:
            print(f"  * [{inc.severity.upper()}] {inc.defect_type.upper()}: {inc.description}")

def print_qa_response(qa_res):
    print("\n" + "="*80)
    print(" [GROUNDED QA] QUESTION ANSWERING & CITATION REPORT")
    print("="*80)
    print(f"  * Question: \"{qa_res.question}\"")
    print(f"  * Abstention Status: {'YES (Declined - Topic not in document)' if qa_res.is_abstention else 'NO (Answer Grounded)'}")
    print(f"  * Refusal Guardrail Triggered: {'YES (Subjective legal advice declined)' if qa_res.is_refusal else 'NO'}")
    print(f"\n  [ANSWER]:\n  {qa_res.answer}")

    if qa_res.cited_clauses:
        print("\n  [GROUNDED CITATIONS & HIGHLIGHT SPANS]:")
        for cite in qa_res.cited_clauses:
            span_info = f" (page {cite.spans[0].page} bbox={cite.spans[0].bbox})" if cite.spans else ""
            print(f"  * Clause {cite.clause_number} - {cite.title} [ID: {cite.clause_id}]{span_info}")
            print(f"    Text: \"{cite.snippet}\"")
    print("="*80 + "\n")

def print_comparison_result(result):
    stats = result.summary_stats
    print("\n" + "="*80)
    print(" [COMPARISON] LEGAL DOCUMENT COMPARISON & SEMANTIC DIFF REPORT")
    print("="*80)
    print(f"  * Baseline Document: {result.doc_id_a} ({stats.get('total_clauses_doc_a', 0)} clauses)")
    print(f"  * Revision Document: {result.doc_id_b} ({stats.get('total_clauses_doc_b', 0)} clauses)")
    print(f"  * Breakdown: +{stats.get('added_count', 0)} Added | -{stats.get('removed_count', 0)} Removed | ~{stats.get('materially_changed_count', 0)} Materially Changed | ={stats.get('unchanged_count', 0)} Unchanged")
    
    # 1. Added
    print("\n" + "-"*80)
    print(f" [+] ADDED CLAUSES ({len(result.added)})")
    print("-"*80)
    if not result.added:
        print("  (No clauses added)")
    for item in result.added:
        print(f"  * Clause {item.clause_number_b} - {item.title_b} [{item.category.upper()}]")
        print(f"    - Meaning Shift: {item.semantic_change_summary}")
        print(f"    - Text: \"{item.text_b.strip()[:100]}...\"")

    # 2. Removed
    print("\n" + "-"*80)
    print(f" [-] REMOVED CLAUSES ({len(result.removed)})")
    print("-"*80)
    if not result.removed:
        print("  (No clauses removed)")
    for item in result.removed:
        print(f"  * Clause {item.clause_number_a} - {item.title_a} [{item.category.upper()}]")
        print(f"    - Meaning Shift: {item.semantic_change_summary}")
        print(f"    - Previous Text: \"{item.text_a.strip()[:100]}...\"")

    # 3. Materially Changed
    print("\n" + "-"*80)
    print(f" [~] MATERIALLY CHANGED CLAUSES ({len(result.materially_changed)})")
    print("-"*80)
    if not result.materially_changed:
        print("  (No clauses materially changed)")
    for item in result.materially_changed:
        print(f"\n  * Clause {item.clause_number_a} -> {item.clause_number_b} [{item.category.upper()}] (Similarity: {item.similarity_score})")
        print(f"    - Title: '{item.title_a}' -> '{item.title_b}'")
        print(f"    - Semantic Change Summary: {item.semantic_change_summary}")
        print(f"    - Baseline: \"{item.text_a.strip()[:85]}...\"")
        print(f"    - Revision: \"{item.text_b.strip()[:85]}...\"")

    # 4. Unchanged
    print("\n" + "-"*80)
    print(f" [=] UNCHANGED CLAUSES ({len(result.unchanged)})")
    print("-"*80)
    for item in result.unchanged:
        print(f"  * Clause {item.clause_number_b} - {item.title_b} [{item.category.upper()}] (Matches baseline Clause {item.clause_number_a})")

    print("="*80 + "\n")

def print_actionable_pack(doc, deadlines, lawyer_prep, rewrite, negotiations, export_ics_path=None):
    print("\n" + "="*80)
    print(f" [ACTIONABLE OUTPUTS PACK] DOCUMENT INTELLIGENCE & DELIVERABLES: {doc.filename}")
    print("="*80)

    # 1. Deadlines & Calendar Events
    print(f"\n  [1. AUTOMATED DEADLINES & OBLIGATIONS (Base Date: {deadlines.effective_date})]")
    if not deadlines.deadlines:
        print("  (No specific deadline timeframes detected)")
    for d in deadlines.deadlines:
        print(f"  * [{d.resolved_date or 'Relative'}] Clause {d.clause_number}: {d.obligation}")
        print(f"    - Party Responsible: {d.party} | Trigger: {d.trigger} ({d.relative_days} days)")

    if export_ics_path:
        with open(export_ics_path, "w", encoding="utf-8") as f:
            f.write(deadlines.ics_content)
        print(f"\n  [iCalendar Export] Generated and saved .ics calendar file to: {export_ics_path}")

    # 2. Lawyer Consultation Preparation Pack
    print("\n" + "-"*80)
    print("  [2. LAWYER-PREP PACK — BRIEFING & INTEGRITY CHECKLIST]")
    print("-"*80)
    facts = lawyer_prep.fact_summary
    print(f"  * Contract: {facts.get('document_name')} ({facts.get('contract_type')})")
    print(f"  * Parties: {', '.join(facts.get('identified_parties', []))}")
    print(f"  * Jurisdiction: {facts.get('governing_law')} | Risk Score: {facts.get('overall_risk_score')}")

    print("\n  [Document Audit Checklist]:")
    for check in lawyer_prep.checklist:
        status_symbol = "[OK]" if check["passed"] else "[FLAG]"
        print(f"    {status_symbol} {check['item']}: {check['details']}")

    print("\n  [Prioritized Questions to Ask Lawyer]:")
    for q in lawyer_prep.prioritized_questions:
        print(f"    - [{q.priority.upper()}] Clause {q.clause_number}: \"{q.question}\"")
        print(f"      (Drafting Reason: {q.context_reason})")

    # 3. Plain-Language & Multilingual Summary
    print("\n" + "-"*80)
    print(f"  [3. PLAIN-LANGUAGE REWRITE — Level: {rewrite.level.upper()} | Language: {rewrite.language.upper()}]")
    print("-"*80)
    print(f"  * Executive Summary:\n    {rewrite.executive_summary}")
    print(f"\n  * Key Rights & Entitlements:\n    {rewrite.key_rights_summary}")

    # 4. Negotiation Counter-Proposals
    print("\n" + "-"*80)
    print(f"  [4. NEGOTIATION COUNTER-PROPOSALS FOR AGGRESSIVE CLAUSES ({len(negotiations)})]")
    print("-"*80)
    if not negotiations:
        print("  (No aggressive clauses detected requiring negotiation counter-proposals)")
    for n in negotiations:
        print(f"\n  * Clause {n.clause_number} ({n.category.upper()}):")
        print(f"    - Original Text Snippet: \"{n.original_text[:110]}...\"")
        print(f"    - Proposed Balanced Alternative:\n      \"{n.proposed_alternative_text}\"")
        print(f"    - One-Line Negotiation Rationale: {n.one_line_rationale}")

    print("="*80 + "\n")

def main():
    parser = argparse.ArgumentParser(description="ClauseLens CLI Inspector")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("generate-samples", help="Generate synthetic flawed sample documents (including saas_terms_v2)")
    
    inspect_parser = subparsers.add_parser("inspect", help="Inspect a PDF or DOCX legal document")
    inspect_parser.add_argument("file_path", type=str, help="Path to PDF or DOCX file")

    profile_parser = subparsers.add_parser("profile", help="Display Document Profile & Missing Clause analysis")
    profile_parser.add_argument("file_path", type=str, help="Path to PDF or DOCX file")

    risk_parser = subparsers.add_parser("risk", help="Perform side-by-side risk analysis & perspective toggle")
    risk_parser.add_argument("file_path", type=str, help="Path to PDF or DOCX file")
    risk_parser.add_argument("--perspective", type=str, default=None, help="Party perspective role (e.g. tenant, landlord, employee, employer, customer, vendor)")

    qa_parser = subparsers.add_parser("qa", help="Ask a grounded legal question over a document")
    qa_parser.add_argument("file_path", type=str, help="Path to PDF or DOCX file")
    qa_parser.add_argument("question", type=str, help="Question to ask")

    compare_parser = subparsers.add_parser("compare", help="Compare two legal documents and generate semantic diff")
    compare_parser.add_argument("file_path_a", type=str, help="Path to baseline PDF or DOCX file")
    compare_parser.add_argument("file_path_b", type=str, help="Path to revised PDF or DOCX file")

    actionable_parser = subparsers.add_parser("actionable", help="Generate complete actionable pack (deadlines, lawyer-prep, rewrite, negotiations)")
    actionable_parser.add_argument("file_path", type=str, help="Path to PDF or DOCX file")
    actionable_parser.add_argument("--effective-date", type=str, default=None, help="Base effective date (YYYY-MM-DD) for deadline resolution")
    actionable_parser.add_argument("--export-ics", type=str, default=None, help="File path to save .ics calendar export")
    actionable_parser.add_argument("--lang", type=str, default="en", choices=["en", "hi", "kn"], help="Language for rewrite summary (en, hi, kn)")
    actionable_parser.add_argument("--level", type=str, default="plain_english", choices=["plain_english", "simple"], help="Reading level for rewrite")
    actionable_parser.add_argument("--perspective", type=str, default=None, help="Party perspective role")

    args = parser.parse_args()

    if args.command == "generate-samples":
        create_all_samples()
        print("Sample documents generated successfully.")
    elif args.command == "inspect":
        parsed, profile = ingest_document(args.file_path)
        risk_profile = analyze_document_risk(parsed)
        print(f"\n[DOC] Document: {parsed.filename} (ID: {parsed.id}, Pages: {parsed.page_count}, Type: {parsed.file_type})")
        print_clause_tree(parsed.clauses)
        print_crossrefs(parsed.crossrefs)
        print_defects(parsed.defects)
        print_profile(profile)
        print_risk_profile(risk_profile)
        print("\n" + "="*80 + "\n")
    elif args.command == "profile":
        parsed, profile = ingest_document(args.file_path)
        print(f"\n[DOC] Document: {parsed.filename} (ID: {parsed.id}, Pages: {parsed.page_count}, Type: {parsed.file_type})")
        print_profile(profile)
        print("\n" + "="*80 + "\n")
    elif args.command == "risk":
        parsed, profile = ingest_document(args.file_path)
        risk_profile = analyze_document_risk(parsed, perspective=args.perspective)
        print(f"\n[DOC] Document: {parsed.filename} (ID: {parsed.id}, Pages: {parsed.page_count}, Type: {parsed.file_type})")
        print_risk_profile(risk_profile)
        print("\n" + "="*80 + "\n")
    elif args.command == "qa":
        parsed, _ = ingest_document(args.file_path)
        qa_res = answer_question(parsed, args.question)
        print_qa_response(qa_res)
    elif args.command == "compare":
        parsed_a, _ = ingest_document(args.file_path_a)
        parsed_b, _ = ingest_document(args.file_path_b)
        result = compare_documents(parsed_a, parsed_b)
        print_comparison_result(result)
    elif args.command == "actionable":
        parsed, _ = ingest_document(args.file_path)
        deadlines = extract_deadlines(parsed, effective_date_str=args.effective_date)
        lawyer_prep = build_lawyer_prep_pack(parsed)
        rewrite = generate_document_rewrite(parsed, level=args.level, language=args.lang)
        negotiations = generate_negotiation_proposals(parsed, perspective=args.perspective)
        print_actionable_pack(parsed, deadlines, lawyer_prep, rewrite, negotiations, export_ics_path=args.export_ics)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
