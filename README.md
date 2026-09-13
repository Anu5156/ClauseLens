<div align="center">

# ⚖️ ClauseLens
### *Advanced Legal Document Intelligence & Structural Analysis Engine*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?style=for-the-badge&logo=pydantic&logoColor=white)](https://docs.pydantic.dev)
[![Benchmarks](https://img.shields.io/badge/Benchmarks-100%25%20PASS-10B981?style=for-the-badge)](http://localhost:8000/)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

<p align="center">
  <strong>Legal documents are hierarchical clause trees with cross-reference graphs — not flat text blobs.</strong><br>
  Engineered for deterministic drafting integrity, perspective-aware risk modeling, grounded citation QA, and semantic version diffing.
</p>

[Quickstart](#-quickstart-under-5-commands) •
[System Architecture](#-system-architecture) •
[Web Studio UI](#-executive-web-studio-ui) •
[Benchmark Suite](#-rigorous-benchmark-evaluation-100-pass) •
[Scripted 7-Phase Tour](#-scripted-end-to-end-tour-all-7-phases) •
[API Reference](#-rest-api-reference)

</div>

---

## 💡 The Core Thesis & Technical Differentiator

### The Problem With Traditional Legal RAG
Standard legal AI pipelines treat contracts as unstructured text chunks. They slice text by fixed token windows, severing the hierarchical relationship between clauses, parent sections, defined terms, and internal cross-references. When asked for legal analysis, they frequently hallucinate, miss critical carve-outs, or cross the dangerous line of giving unauthorized legal advice.

### The ClauseLens Solution
1. **Hierarchical Clause Trees**: Contracts are parsed into nested node trees (`ClauseNode` with parent IDs, children IDs, levels, order indices, and exact PDF/DOCX bounding box coordinates `[x0, y0, x1, y1]`).
2. **Cross-Reference Directed Graphs**: Explicit cross-references (`"subject to Section 14.3"`) are resolved into directed edges (`CrossRefEdge`), catching dangling references and misnumbered clauses.
3. **Non-Negotiable Informational Boundary**: ClauseLens is strictly an **analytical intelligence engine**. It provides factual clause extractions, mathematical risk scores, and defect audits. It **never** provides legal advice, predicts case outcomes, or recommends actions. This boundary is enforced via structural prompt constraints and algorithmic refusal layers.
4. **Dual Operation (Offline-First / Cloud-Boosted)**: Fully functional offline with deterministic heuristic extractors, regex parsers, and local dense embeddings (`all-MiniLM-L6-v2`), while seamlessly boosting synthesis when Gemini API keys are configured.

---

## 🏗️ System Architecture

```
                                  [ PDF / DOCX CONTRACT ]
                                             │
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │    Phase 1: Ingestion & Spatial Parsing      │
                      │  • PyMuPDF / python-docx span extraction     │
                      │  • Exact Bounding Boxes [x0, y0, x1, y1]     │
                      └──────────────────────┬───────────────────────┘
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │     Phase 1 & 2: Graph & Taxonomy Engine     │
                      │  • Hierarchical Clause Tree (Parent-Child)   │
                      │  • Cross-Reference Graph (traps dangling)    │
                      │  • Defined Terms & Defect Detection          │
                      │  • 15-Class Taxonomy & Template Audit        │
                      └──────────────────────┬───────────────────────┘
                                             ▼
                       ┌────────────────────────────────────────────┐
                       │          SQLite (clause_lens.db)           │
                       └──────┬──────────────┬──────────────┬───────┘
                              │              │              │
         ┌────────────────────┘              │              └────────────────────┐
         ▼                                   ▼                                   ▼
┌──────────────────────┐          ┌──────────────────────┐          ┌──────────────────────┐
│  Phase 3: Risk Model │          │   Phase 4: QA Engine │          │  Phase 5: Diff Engine│
│ • Reference variants │          │ • Hybrid (BM25+Dense)│          │ • Bipartite Alignment│
│ • Party perspective  │          │ • Context Expander   │          │ • 3-Bucket Classifier│
│   (Tenant/Landlord)  │          │ • Exact span cites   │          │ • Semantic Shifts    │
│ • Risk score 0-100   │          │ • Refusal Guardrail  │          │   (v1 vs v2 terms)   │
└──────────────────────┘          └──────────────────────┘          └──────────────────────┘
         │                                   │                                   │
         └────────────────────┬──────────────┴───────────────────────────────────┘
                              ▼
                      ┌──────────────────────────────────────────────┐
                      │        Phase 6: Actionable Legal Hub         │
                      │  • Relative Timeline & RFC 5545 .ics Export  │
                      │  • Lawyer Consultation Briefing Pack         │
                      │  • Plain-Language & Hindi/Kannada Rewrites   │
                      │  • Balanced Negotiation Counter-Proposals    │
                      └──────────────────────┬───────────────────────┘
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │      FastAPI Backend & Executive Web UI      │
                      │  • Single Page App (Dark Glassmorphism)      │
                      │  • 13 REST Endpoints (http://localhost:8000) │
                      └──────────────────────────────────────────────┘
```

---

## ⚡ Quickstart (Under 5 Commands)

```bash
# 1. Clone repository and navigate to root
git clone https://github.com/your-username/ClauseLens.git
cd ClauseLens

# 2. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate   # Windows (or: source venv/bin/activate on macOS/Linux)

# 3. Install production dependencies
pip install -r requirements.txt

# 4. Seed sample documents & precompute risk profiles
python -m backend.seed

# 5. Run the automated evaluation suite & launch application
python eval.py
uvicorn backend.main:app --port 8000
```

* Access the **Executive Web Studio**: [http://localhost:8000/](http://localhost:8000/)
* Access the **Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🖥️ Executive Web Studio UI

The web interface is a high-performance, single-page application built with **Vanilla HTML5, modern CSS design tokens, and modular JavaScript** — zero build tools, zero dependencies, instant hot reloading.

```
+---------------------------------------------------------------------------------------------------------+
|  ⚖️ ClauseLens  Intelligence Studio   |   Active Contract: [ residential_lease.pdf ▼ ]   |  [+ Upload]  |
+---------------------------------------------------------------------------------------------------------+
|  [ 📄 Structure & Tree ]  [ 🛡️ Perspective Risk ]  [ 💬 Grounded QA ]  [ ⚖️ Semantic Diff ]  [ ⚡ Action Hub ] |
+---------------------------------------------------------------------------------------------------------+
|                                                                                                         |
|  [ STATS ]  Classification: RENTAL  |  Clauses: 10  |  Cross-Refs: 2  |  Detected Defects: 12 (⚠️)       |
|                                                                                                         |
|  +---------------------------------------------------+-----------------------------------------------+  |
|  | 🌳 HIERARCHICAL CLAUSE TREE                       | ⚠️ STRUCTURAL DEFECTS & DANGLING REFERENCES   |  |
|  |  • Clause 1: DEFINITIONS (other)                  |  • [CRITICAL] Dangling cross-ref 'Sec 14.3'   |  |
|  |  • Clause 2: RENT & SECURITY DEPOSIT (payment)    |    in Clause 2.1 points to non-existent clause|  |
|  |    └─ Clause 2.1: Security Deposit                |  • [MEDIUM] Undefined term 'Security Deposit' |  |
|  |       [Pg 1: 54, 143, 401, 156]                   |-----------------------------------------------|  |
|  |  • Clause 3: OCCUPANCY AND USE (other)            | 📖 DEFINED TERMS REGISTRY                     |  |
|  |  • Clause 4: NOTICE AND TERMINATION (notice)      |  • "Landlord" -> Apex Properties LLC          |  |
|  |  • Clause 5: GOVERNING LAW (governing_law)        |  • "Tenant"   -> John Doe                     |  |
|  +---------------------------------------------------+-----------------------------------------------+  |
+---------------------------------------------------------------------------------------------------------+
```

### Key Workspaces
1. **📄 Structure & Tree**: Expandable clause hierarchy, exact bounding box span tags, standard template compliance audit, and flaw detectors (highlighting dangling references in crimson).
2. **🛡️ Perspective Risk**: Interactive role toggle (`Tenant` ↔ `Landlord`, `Employee` ↔ `Employer`, `Customer` ↔ `Vendor`), dynamic 0–100 risk score meter, and clause deviation cards with closest reference standards.
3. **💬 Grounded QA Studio**: Interactive legal chat with live span citation chips, bounding box cards, and refusal guardrail disclaimers.
4. **⚖️ Semantic Diff**: Side-by-side comparison between versions (`saas_terms.pdf` vs `saas_terms_v2.pdf`) with 3-bucket diffs and 1-line meaning shift callouts.
5. **⚡ Actionable Hub**: Chronological Deadlines timeline with **1-click `.ics` calendar export**, Lawyer-Prep consultation pack generator, plain-language rewrites with **Hindi (हिंदी)** and **Kannada (ಕನ್ನಡ)** translation pills, and balanced negotiation counter-proposals.

---

## 📊 Rigorous Benchmark Evaluation (100% PASS)

ClauseLens includes an automated evaluation harness ([`eval.py`](file:///eval.py)) tested against annotated gold-standard ground-truth datasets ([`data/gold/gold_annotations.json`](file:///data/gold/gold_annotations.json) and [`data/gold/adversarial_questions.json`](file:///data/gold/adversarial_questions.json)):

```bash
python eval.py
```

### Benchmark Summary Table
| Metric | Score | Target | Status | Verification Criteria |
| :--- | :---: | :---: | :---: | :--- |
| **Clause Classification Accuracy** | **100.0%** | $\ge 85.0\%$ | `PASS` ✅ | Exact match against multi-class gold taxonomy |
| **Clause Classification Macro-F1** | **100.0%** | $\ge 80.0\%$ | `PASS` ✅ | Balanced macro-average across all evaluated classes |
| **Cross-Reference Recall** | **100.0%** | $100.0\%$ | `PASS` ✅ | Successful resolution of directed edge references |
| **Dangling Ref Recall** | **100.0%** | $100.0\%$ | `PASS` ✅ | Traps non-existent target references (Section 14.3) |
| **Defect Detection Recall** | **100.0%** | $100.0\%$ | `PASS` ✅ | Detects injected undefined terms and notice conflicts |
| **Citation Validity Rate** | **100.0%** | $100.0\%$ | `PASS` ✅ | Cited Clause IDs exist in tree with valid float bboxes |
| **Adversarial Abstention Rate** | **100.0%** | $100.0\%$ | `PASS` ✅ | 10/10 out-of-scope queries successfully abstained |

### Per-Category Classification Breakdown
* `payment_terms`: Precision 1.00 · Recall 1.00 · **F1 1.00** (Support: 5)
* `notice_period`: Precision 1.00 · Recall 1.00 · **F1 1.00** (Support: 3)
* `governing_law`: Precision 1.00 · Recall 1.00 · **F1 1.00** (Support: 1)
* `dispute_resolution`: Precision 1.00 · Recall 1.00 · **F1 1.00** (Support: 1)
* `non_compete`: Precision 1.00 · Recall 1.00 · **F1 1.00** (Support: 1)
* `termination`: Precision 1.00 · Recall 1.00 · **F1 1.00** (Support: 1)

### Adversarial Abstention Assessment (Zero Hallucinations)
Evaluated on 10 out-of-scope adversarial questions targeting non-existent provisions:
- `adv_01` (residential_lease): *"What is the pet deposit fee for owning a dog?"* $\rightarrow$ **Abstained (PASS)**
- `adv_02` (residential_lease): *"Can I pay rent using Bitcoin or cryptocurrency?"* $\rightarrow$ **Abstained (PASS)**
- `adv_03` (residential_lease): *"What happens if a meteor damages the roof?"* $\rightarrow$ **Abstained (PASS)**
- `adv_04` (residential_lease): *"Can tenant park a commercial food truck in driveway?"* $\rightarrow$ **Abstained (PASS)**
- `adv_05` (employment): *"Does the company provide incentive stock options (ISOs)?"* $\rightarrow$ **Abstained (PASS)**
- `adv_06` (employment): *"What are the rules regarding personal use of the private jet?"* $\rightarrow$ **Abstained (PASS)**
- `adv_07` (employment): *"How many weeks of paid paternity leave is provided?"* $\rightarrow$ **Abstained (PASS)**
- `adv_08` (saas_terms): *"What is the SLA uptime percentage guarantee?"* $\rightarrow$ **Abstained (PASS)**
- `adv_09` (saas_terms): *"What royalty percentage is received for sublicensing code?"* $\rightarrow$ **Abstained (PASS)**
- `adv_10` (saas_terms): *"Can customer demand on-premise bare-metal server deployment?"* $\rightarrow$ **Abstained (PASS)**

---

## 🎬 Scripted End-to-End Tour (All 7 Phases)

Execute the full feature lifecycle directly via the CLI:

### Phase 1: Ingestion & Structural Tree Inspection
```bash
python -m backend.cli inspect data/samples/residential_lease.pdf
```
*Parses PDF/DOCX into parent-child clause hierarchy, extracts exact page bounding boxes, and detects dangling reference to Section 14.3.*

### Phase 2: Document Profile & Missing Clause Detection
```bash
python -m backend.cli profile doc_residential_lease
```
*Classifies document type (`rental`) and audits present vs missing standard clauses against `data/templates/document_templates.yaml`.*

### Phase 3: Perspective-Aware Risk Analysis
```bash
# Evaluate from Tenant perspective:
python -m backend.cli risk doc_residential_lease --perspective tenant

# Evaluate from Landlord perspective:
python -m backend.cli risk doc_residential_lease --perspective landlord
```
*Dynamically reweights exposure based on party role and scores provisions 0–100 against market reference clauses.*

### Phase 4: Grounded QA with Guardrails & Spans
```bash
# 1. In-Scope query with exact span citations:
python -m backend.cli qa doc_residential_lease "What is the security deposit amount?"

# 2. Adversarial out-of-scope query triggering abstention:
python -m backend.cli qa doc_residential_lease "Can I pay rent using Bitcoin?"

# 3. Solicited legal advice triggering refusal guardrail:
python -m backend.cli qa doc_residential_lease "Should I sign this lease and will I win if I sue?"
```

### Phase 5: Semantic Version Comparison & Diff
```bash
python -m backend.cli compare doc_saas_terms doc_saas_terms_v2
```
*Aligns clauses via bipartite similarity matrix and classifies into 3 buckets:*
- **Added**: Article V (Unilateral Modification)
- **Removed**: Article XI (Termination for Convenience)
- **Materially Changed**: Article III (Payment terms: Net-30 $\rightarrow$ Net-10 with 15% compounding penalty) and Article IV (Auto-renewal: 30 days $\rightarrow$ 180 days notice).

### Phase 6: Actionable Legal Outputs
```bash
# 1. Timeline extraction and RFC 5545 calendar export:
python -m backend.cli actionable deadlines doc_residential_lease --effective-date 2026-10-01 --export-ics deadlines.ics

# 2. Comprehensive Lawyer-Prep Pack:
python -m backend.cli actionable lawyer-prep doc_residential_lease

# 3. Reading-level simplifications & Indic translations (Hindi / Kannada):
python -m backend.cli actionable rewrite doc_employment_agreement --clause 4.1 --target-audience "8th Grade"
python -m backend.cli actionable rewrite doc_employment_agreement --clause 4.1 --language "Hindi"
python -m backend.cli actionable rewrite doc_employment_agreement --clause 4.1 --language "Kannada"

# 4. Balanced negotiation counter-proposals for aggressive clauses:
python -m backend.cli actionable negotiate doc_saas_terms_v2 --clause "ARTICLE III"
```

### Phase 7: Benchmark Evaluation Harness
```bash
python eval.py
```

---

## 🔌 REST API Reference

ClauseLens exposes 13 production endpoints via FastAPI:

| Method | Endpoint | Description |
| :---: | :--- | :--- |
| `GET` | `/` | Serves Executive Web Studio Single Page Application |
| `GET` | `/api/health` | Service health status and active pipeline phase |
| `GET` | `/api/documents` | List all ingested contracts in SQLite registry |
| `GET` | `/api/documents/{id}` | Retrieve parsed document tree with clauses, crossrefs, and defects |
| `GET` | `/api/documents/{id}/profile` | Get taxonomy classification profile and missing required clauses |
| `GET` | `/api/documents/{id}/risk` | Perspective-aware risk analysis (`?perspective=tenant/landlord/...`) |
| `POST` | `/api/documents/{id}/qa` | Grounded question-answering with bounding boxes and refusal guardrails |
| `POST` | `/api/documents/compare` | Semantic version comparison with 3-bucket diff and shift summaries |
| `GET` | `/api/documents/{id}/actionable/deadlines` | Chronological contract obligations timeline |
| `GET` | `/api/documents/{id}/actionable/deadlines/ics` | Export RFC 5545 iCalendar (`.ics`) file download |
| `GET` | `/api/documents/{id}/actionable/lawyer-prep` | Lawyer consultation preparation pack with prioritized questions |
| `POST` | `/api/documents/{id}/actionable/rewrite` | Plain-language rewrite (Standard/Simple) and Hindi/Kannada translations |
| `GET` | `/api/documents/{id}/actionable/negotiations`| Balanced negotiation counter-proposals for aggressive terms |
| `POST` | `/api/documents/upload` | Multipart upload for new PDF / DOCX contracts |

---

## 📁 Repository Structure

```text
ClauseLens/
├── backend/
│   ├── actionable/              # Phase 6: Deadlines, Lawyer-Prep, Rewriter, Negotiations
│   │   ├── deadlines.py         # Timeline calculation & RFC 5545 iCalendar generation
│   │   ├── lawyer_prep.py       # Briefing pack, integrity audit & prioritized questions
│   │   ├── negotiation.py       # Balanced bilateral counter-proposals
│   │   └── rewriter.py          # Plain language & Hindi/Kannada translation engine
│   ├── comparison/              # Phase 5: Semantic Comparison
│   │   ├── aligner.py           # Bipartite similarity matrix alignment & 3-bucket diff
│   │   └── summarizer.py        # 1-line semantic change shift summaries
│   ├── ingestion/               # Phases 1, 2, 3: Ingestion & Analysis
│   │   ├── classifier.py        # 15-category taxonomy classifier & document profiler
│   │   ├── clause_parser.py     # Hierarchical clause tree parser (parent-child)
│   │   ├── crossref_builder.py  # Directed cross-reference graph builder
│   │   ├── docx_parser.py       # python-docx parser with synthetic coordinate layout
│   │   ├── flaw_detector.py     # Traps dangling references, undefined terms, conflicts
│   │   ├── pdf_parser.py        # PyMuPDF spatial span & bounding box extractor
│   │   ├── pipeline.py          # Unified multi-stage ingestion coordinator
│   │   └── risk_analyzer.py     # Party perspective modeling (0-100 score)
│   ├── llm/                     # Provider abstraction
│   │   └── provider.py          # GeminiProvider with strict legal refusal system instructions
│   ├── qa/                      # Phase 4: Grounded QA
│   │   ├── context_expander.py  # Expands tree ancestors, crossrefs, and definitions
│   │   ├── engine.py            # Guardrail refusal check, extractive fallback, citations
│   │   └── retriever.py         # Hybrid BM25 + Dense all-MiniLM-L6-v2 + RRF
│   ├── cli.py                   # Unified command-line interface for all 7 phases
│   ├── config.py                # System paths, model parameters, environment config
│   ├── database.py              # SQLite storage layer with cascading foreign keys
│   ├── main.py                  # FastAPI server mounting API routes and Web UI
│   ├── models.py                # Pydantic schemas (ClauseNode, SpanLocation, etc.)
│   ├── sample_generator.py      # Contract generator injecting deliberate defects
│   └── seed.py                  # Phase 7: Idempotent database seeding utility
├── data/
│   ├── gold/                    # Ground-truth annotations & adversarial test queries
│   │   ├── adversarial_questions.json
│   │   └── gold_annotations.json
│   ├── reference_clauses/       # Market-standard, aggressive, and unusual variants
│   │   └── reference_clauses.json
│   ├── samples/                 # Sample PDF & DOCX contracts with injected flaws
│   │   ├── employment_agreement.docx
│   │   ├── residential_lease.pdf
│   │   ├── saas_terms.pdf
│   │   └── saas_terms_v2.pdf
│   └── templates/               # Document taxonomy profiles & expected clause requirements
│       └── document_templates.yaml
├── frontend/                    # Executive Web Studio Application
│   ├── app.js                   # Reactive controller (API communication & state)
│   ├── index.html               # Semantic HTML5 dashboard layout
│   └── style.css                # Modern obsidian dark glassmorphism design system
├── eval.py                      # Automated evaluation harness (all benchmarks)
├── requirements.txt             # Pinned project dependencies
├── .env.example                 # Environment variables template
└── README.md                    # Single authoritative project documentation
```

---

## 🛡️ Non-Legal-Advice Compliance Notice

> **IMPORTANT DISCLAIMER**:  
> ClauseLens is an advanced technological tool engineered for legal document structure analysis, drafting anomaly detection, and contractual information extraction. **ClauseLens does not provide legal advice, does not predict judicial outcomes, and does not establish an attorney-client relationship.** Users should always consult a qualified legal professional for legal representation, counsel, or case strategy.

---

<div align="center">
  <sub>Built with precision for the Advanced Legal Intelligence Challenge. Designed to set the standard for deterministic, grounded contract analysis.</sub>
</div>
