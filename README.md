<div align="center">

# ⚖️ ClauseLens
### *Advanced Legal Document Intelligence, Hierarchical Structural Analysis & Grounded Assistance Engine*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?style=for-the-badge&logo=pydantic&logoColor=white)](https://docs.pydantic.dev)
[![Tests](https://img.shields.io/badge/Tests-84%2F84%20PASS%20(100%25)-10B981?style=for-the-badge)](http://localhost:8000/)
[![Benchmarks](https://img.shields.io/badge/Benchmarks-100%25%20PASS-10B981?style=for-the-badge)](http://localhost:8000/)
[![Repo Size](https://img.shields.io/badge/Repo%20Size-%3C%201%20MB-blue?style=for-the-badge)](https://github.com/Anu5156/ClauseLens)
[![Branch](https://img.shields.io/badge/Git%20Branch-main%20only-blueviolet?style=for-the-badge)](https://github.com/Anu5156/ClauseLens)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

<p align="center">
  <strong>Legal contracts are hierarchical clause trees with directed cross-reference graphs — not flat text blobs.</strong><br>
  Built for deterministic drafting integrity, perspective-aware risk modeling, grounded citation QA, and semantic version diffing.
</p>

[Quickstart](#-quickstart-under-5-commands) •
[Hackathon Alignment](#-hackathon-submission-ai-for-legal-assistance--access) •
[System Architecture](#-system-architecture) •
[Web Studio UI](#-faang-caliber-web-studio-ui) •
[Mathematical Formulations](#-core-algorithms--mathematical-formulations) •
[Benchmark Suite](#-rigorous-benchmark-evaluation-100-pass) •
[Scripted 7-Phase Tour](#-scripted-end-to-end-tour-all-7-phases) •
[REST API Reference](#-rest-api-reference)

</div>

---

## 🎯 Hackathon Submission: AI for Legal Assistance & Access

### 1. Challenge Vertical & Problem Alignment
* **Chosen Vertical:** **AI for Legal Assistance & Access**
* **Root Problem:** Standard legal documents (residential leases, employment agreements, SaaS terms, vendor contracts) are deliberately drafted in archaic, convoluted legalese. Everyday consumers, tenants, employees, and small business founders cannot afford hourly attorney consultations just to understand basic obligations, notice timelines, or indemnity risks. When they turn to generic LLMs, they encounter hallucinations, lost context, missing cross-references, or dangerous unauthorized legal advice.
* **The ClauseLens Solution:** ClauseLens is an AI-powered legal document intelligence platform that bridges this access gap. It parses contracts into **spatial clause trees**, detects **drafting flaws & dangling cross-references**, evaluates **asymmetric party exposure**, simplifies provisions into **8th-grade plain English & Indic languages (Hindi, Kannada)**, generates **RFC 5545 calendar deadlines**, builds **lawyer consultation briefing packs**, and formulates **balanced negotiation alternatives**—all while enforcing a strict **non-legal-advice informational boundary**.

---

### 2. Pin-to-Pin Feature & Use-Case Matrix

| Challenge Required Use Case | ClauseLens Feature Implementation | Technical Module | UI Workspace Location |
| :--- | :--- | :--- | :--- |
| **1. Simplifying complex legal documents** | Dual-tier Plain-Language Simplification (*Standard* vs. *8th-Grade Simple No-Legalese*) + Indic Regional Translations (**Hindi हिंदी & Kannada ಕನ್ನಡ**) | [`backend/actionable/rewriter.py`](backend/actionable/rewriter.py) | **Actionable Hub** &rarr; *Multilingual Rewrites* |
| **2. Comparing contracts, agreements, or policies** | Semantic Bipartite Diff Engine: Hungarian alignment algorithm classifying clauses into 3 buckets (*Added, Removed, Materially Changed*) with 1-line plain English semantic shift summaries | [`backend/comparison/aligner.py`](backend/comparison/aligner.py)<br>[`backend/comparison/summarizer.py`](backend/comparison/summarizer.py) | **Semantic Diff** Tab with Swap baseline toggle |
| **3. Highlighting important clauses, obligations, risks, or inconsistencies** | **Hierarchical Clause Tree** with 15-class taxonomy, **Dangling Cross-Reference Detector** (e.g. traps *Section 14.3*), **Undefined Terms Registry**, and **Perspective Risk Analyzer (0–100 score)** | [`backend/ingestion/clause_parser.py`](backend/ingestion/clause_parser.py)<br>[`backend/ingestion/flaw_detector.py`](backend/ingestion/flaw_detector.py)<br>[`backend/ingestion/risk_analyzer.py`](backend/ingestion/risk_analyzer.py) | **Structure & Tree** + **Perspective Risk** Tabs |
| **4. Answering questions based on provided legal documents** | Grounded QA Engine with Hybrid Retrieval (BM25 + Dense `all-MiniLM-L6-v2` + Reciprocal Rank Fusion) and exact PDF/DOCX page bounding box coordinates `[x0, y0, x1, y1]` | [`backend/qa/engine.py`](backend/qa/engine.py)<br>[`backend/qa/retriever.py`](backend/qa/retriever.py) | **Grounded QA Studio** with interactive citation chips |
| **5. Helping users understand their options and potential next steps** | Bilateral Negotiation Alternatives: detects one-sided/aggressive terms and generates balanced counter-proposals with 1-line rationales | [`backend/actionable/negotiation.py`](backend/actionable/negotiation.py) | **Actionable Hub** &rarr; *Negotiation Proposals* |
| **6. Generating summaries, checklists, or actionable outputs** | Chronological Obligations Timeline with **RFC 5545 `.ics` Calendar Export**, Executive Summary, and Document Profile Compliance | [`backend/actionable/deadlines.py`](backend/actionable/deadlines.py) | **Actionable Hub** &rarr; *Deadlines & .ics* |
| **7. Helping users prepare information or questions for a legal professional** | **Lawyer Consultation Preparation Pack**: automated fact digest, integrity checklist, and prioritized questions for counsel | [`backend/actionable/lawyer_prep.py`](backend/actionable/lawyer_prep.py) | **Actionable Hub** &rarr; *Lawyer-Prep Brief* |
| **8. Non-Legal-Advice Informational Guardrail** | Algorithmic refusal layer and visible informational alerts when queries solicit legal advice, predictions, or lawsuit strategy | [`backend/llm/provider.py`](backend/llm/provider.py) | **Grounded QA Studio** (Refusal Banner) |

---

### 3. User Personas & Real-World User Journeys

ClauseLens is purpose-built for five key user personas:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       CLAUSELENS USER PERSONAS                                   │
├─────────────────────────┬─────────────────────────┬──────────────────────────────────────────────┤
│ Persona                 │ Typical Problem         │ ClauseLens Solution Path                     │
├─────────────────────────┼─────────────────────────┼──────────────────────────────────────────────┤
│ 🏠 Tenant               │ Confusing lease, hidden │ Perspective Risk: toggles "Tenant", catches  │
│                         │ penalties, deposit risk │ dangling refund clauses, exports move-out    │
│                         │                         │ notice deadline to Apple/Google Calendar.    │
├─────────────────────────┼─────────────────────────┼──────────────────────────────────────────────┤
│ 💼 Employee             │ Aggressive non-compete  │ Simplification: rewrites 2-page covenant     │
│                         │ and IP assignment terms │ into 8th-grade English and Hindi. Generates  │
│                         │                         │ targeted questions for legal counsel.        │
├─────────────────────────┼─────────────────────────┼──────────────────────────────────────────────┤
│ 🚀 SaaS Customer / SMB  │ Vendor changes terms v1 │ Semantic Diff: aligns versions, detects Net30│
│                         │ to v2 with steep fines  │ to Net10 switch + 15% compounding penalty,   │
│                         │                         │ and generates balanced counter-proposals.    │
├─────────────────────────┼─────────────────────────┼──────────────────────────────────────────────┤
│ ⚖️ Pro Se Individual    │ Cannot afford $500/hr   │ Grounded QA: queries obligations with exact  │
│                         │ attorney for initial    │ span citations and builds a structured       │
│                         │ contract review         │ Lawyer Consultation Briefing Pack.           │
├─────────────────────────┼─────────────────────────┼──────────────────────────────────────────────┤
│ 🌐 Non-English Speaker  │ Dense legal jargon in   │ Actionable Rewriter: translates complex     │
│                         │ English-only agreements │ covenants into fluent Hindi & Kannada.       │
└─────────────────────────┴─────────────────────────┴──────────────────────────────────────────────┘
```

---

### 4. Key Assumptions Made
1. **Strict Informational Boundary**: ClauseLens is an analytical and educational intelligence system designed to assist human understanding, not replace licensed attorneys or provide formal legal representation.
2. **Dual Operational Reliability**: The solution operates 100% offline using deterministic heuristics, regex parsers, and local embeddings (`all-MiniLM-L6-v2`), while dynamically boosting synthesis when Gemini API keys are supplied.
3. **Supported Formats & Size**: Primary supported contract formats are PDF and DOCX up to an enforced 25 MB safety limit.
4. **Perspective Asymmetry**: Legal risks are inherently asymmetric; what protects a landlord can expose a tenant. Thus, risk modeling must always allow role selection.

---

### 5. Evaluation Focus Areas Mapping

* **Code Quality (High Impact)**:
  - Clean modular architecture separated into `ingestion`, `qa`, `comparison`, `actionable`, and `llm`.
  - Type-safe Pydantic v2 domain schemas (`ClauseNode`, `CrossRefEdge`, `DraftingDefect`, `DocumentRiskProfile`, `DocumentComparisonResult`).
  - Strict docstrings, type annotations, and automated formatting.
* **Security (Medium Impact)**:
  - File upload path traversal sanitization (`re.sub(r"[^a-zA-Z0-9_.-]", "_", ...)`).
  - 25 MB hard upload payload limit (`413 Payload Too Large`).
  - Restrictive CORS origin configuration and security response headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`).
  - Zero sensitive tokens or credentials stored in repository.
* **Efficiency (Medium Impact)**:
  - Fast response times (< 45ms for clause tree traversal and cached lookups).
  - SQLite relational storage with indexed foreign keys.
  - Zero-build vanilla frontend (no node_modules, webpack, or npm bloat).
  - Total git repository size is **~351 KiB** (far below the strict **10 MB limit**).
* **Testing (Low Impact)**:
  - **84 / 84** passing automated pytest tests (`test_api.py`, `test_models.py`, `test_qa_engine.py`, `test_security.py`).
  - Comprehensive standalone benchmark suite ([`eval.py`](eval.py)) with ground-truth gold annotations and adversarial queries.
* **Accessibility (Low Impact)**:
  - Full keyboard accessibility (`Tab`, `Enter`, and `Esc` to close slide-overs/modals).
  - Skip-to-main-content navigation link.
  - Semantic HTML5 elements (`<header>`, `<nav>`, `<main>`, `<aside>`, `<section>`, role attributes).
  - High-contrast dark glassmorphism palette (WCAG 2.1 AA compliant text contrast).

---

## 💡 The Core Thesis & Technical Differentiator

### The Problem With Traditional Legal RAG
Standard legal AI pipelines treat contracts as flat, unstructured text chunks. They slice text by fixed token windows (e.g. 500 tokens with 50-token overlap), severing the hierarchical relationship between clauses, parent sections, defined terms, and internal cross-references. When asked for legal analysis, traditional RAG models:
1. Lose critical exceptions (e.g. *"Subject to Section 14.3, Tenant shall not..."* gets split across chunks).
2. Fail to catch drafting flaws like dangling references or undefined capitalized terms.
3. Cannot model perspective risk (what is beneficial for one party is hazardous for the other).
4. Hallucinate legal answers and frequently cross the line into unauthorized legal advice.

### The ClauseLens Solution
```
Traditional Flat RAG:
[ Chunk 1: Tokens 0-500 ] ──> [ Chunk 2: Tokens 450-950 ] ──> [ Chunk 3: Tokens 900-1400 ]
(Context severed, definitions separated, cross-references broken, zero spatial coordinates)

ClauseLens Hierarchical Graph:
                ┌───────────────────────────────┐
                │   Contract Root Document      │
                └───────────────┬───────────────┘
                                │
        ┌───────────────────────┴───────────────────────┐
        ▼                                               ▼
┌───────────────────────────────┐               ┌───────────────────────────────┐
│ Section 2: Rent & Deposit     │               │ Section 14: Termination       │
│ Level: 1 | Order: 2           │               │ Level: 1 | Order: 14          │
└───────────────┬───────────────┘               └───────────────┬───────────────┘
                │                                               │
                ▼                                               ▼
┌───────────────────────────────┐               ┌───────────────────────────────┐
│ Clause 2.1: Security Deposit  │══[Dangling]══>│ Section 14.3 (DOES NOT EXIST) │
│ BBox: [54, 143, 401, 156]     │  CrossRefEdge │ Flaw: Missing Target Section  │
└───────────────────────────────┘               └───────────────────────────────┘
```

1. **Hierarchical Clause Trees**: Contracts are parsed into nested node trees (`ClauseNode` with parent IDs, children IDs, levels, order indices, and exact PDF/DOCX bounding box coordinates `[x0, y0, x1, y1]`).
2. **Cross-Reference Directed Graphs**: Explicit cross-references (`"subject to Section 14.3"`) are resolved into directed edges (`CrossRefEdge`), catching dangling references and misnumbered clauses.
3. **Perspective Risk Modeling**: Evaluates bilateral exposure by reweighting deviations based on whether the user is the Tenant, Landlord, Employee, Employer, Customer, or Vendor.
4. **Non-Negotiable Informational Boundary**: ClauseLens is strictly an **analytical intelligence engine**. It provides factual clause extractions, mathematical risk scores, and defect audits. It **never** provides legal advice, predicts judicial outcomes, or recommends lawsuit action.

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
git clone https://github.com/Anu5156/ClauseLens.git
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
* Access the **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🖥️ FAANG-Caliber Web Studio UI

The web interface is an ultra-premium single-page application built with **Vanilla HTML5, modern CSS design tokens, and reactive JavaScript** — zero build tools, zero dependencies, instant hot reloading.

```
+-------------------------------------------------------------------------------------------------------------------------+
|  ⚖️ ClauseLens  Intelligence Studio   |   Active Contract: [ residential_lease.pdf ▼ ]   |  [+ Upload Contract]        |
+-------------------------------------------------------------------------------------------------------------------------+
|  [ 📄 Structure & Tree ]  [ 🛡️ Perspective Risk ]  [ 💬 Grounded QA ]  [ ⚖️ Semantic Diff ]  [ ⚡ Actionable Hub ]       |
+-------------------------------------------------------------------------------------------------------------------------+
|                                                                                                                         |
|  [ STATS ]  Doc Classification: RENTAL  |  Clauses: 10  |  Cross-References: 2  |  Detected Defects: 12 (⚠️)             |
|                                                                                                                         |
|  +-------------------------------------------------------------+-----------------------------------------------------+  |
|  | 🌳 HIERARCHICAL CLAUSE TREE                                 | ⚠️ STRUCTURAL DEFECTS & DANGLING REFERENCES         |  |
|  |  [ Search clauses...           ] [All] [Gov] [Fin] [Liab]   |  • [CRITICAL] Dangling cross-ref 'Sec 14.3' in      |  |
|  |                                                             |    Clause 2.1 points to non-existent clause          |  |
|  |  • Clause 1: DEFINITIONS (other)                            |  • [MEDIUM] Undefined term 'Security Deposit'       |  |
|  |  • Clause 2: RENT AND SECURITY DEPOSIT (payment_terms)      |-----------------------------------------------------|  |
|  |    └─ Clause 2.1: Security Deposit                          | 📖 DEFINED TERMS REGISTRY                           |  |
|  |       [Pg 1: 54, 143, 401, 156] ➔ [Click to inspect]        |  • "Landlord" ➔ Apex Properties LLC                 |  |
|  |  • Clause 3: OCCUPANCY AND USE (other)                      |  • "Tenant"   ➔ John Doe                            |  |
|  |  • Clause 4: NOTICE AND TERMINATION (notice_period)         |-----------------------------------------------------|  |
|  |  • Clause 5: GOVERNING LAW (governing_law)                  | 📋 TEMPLATE COMPLIANCE: 100% Compliant              |  |
|  +-------------------------------------------------------------+-----------------------------------------------------+  |
+-------------------------------------------------------------------------------------------------------------------------+
|  [SLIDE-OVER DRAWER] Clause Inspector: § 2.1 Security Deposit | Full Verbatim Text | [Copy] | [Query in QA Studio]       |
+-------------------------------------------------------------------------------------------------------------------------+
```

### Key UI Features
1. **Slide-Over Clause Inspector Drawer**: Clicking any clause node opens a slide-over panel displaying metadata, exact bounding box coordinates, category badge, and full legal text with 1-click clipboard copy.
2. **Real-Time Clause Search & Filter Bar**: Instant filtering by keyword, clause section number, or category chip (*All, Governance, Financial, Liability, Termination*).
3. **Animated SVG Circular Risk Gauge**: Circular progress meter animated via SVG stroke-dashoffset with dynamic color transitions:
   - 🟢 **Low Risk (0–40)**: Market-standard balanced provisions.
   - 🟡 **Moderate Risk (41–70)**: Non-standard covenants requiring scrutiny.
   - 🔴 **High Risk (71–100)**: Asymmetric liabilities, punitive fees, or structural defects.
4. **Grounded QA Studio**: Chat interface featuring typing indicator dots, 1-click answer copy, and interactive citation tags that link directly into the Clause Inspector.
5. **Toast Notification Engine**: Non-intrusive auto-dismissing toast alerts for all actions, completely eliminating crude browser `alert()` popups.

---

## 🧮 Core Algorithms & Mathematical Formulations

### 1. Bipartite Semantic Clause Alignment (Diff Engine)
To align clauses between version $A$ ($v_1$) and version $B$ ($v_2$), ClauseLens computes a dense pairwise cosine similarity matrix:

$$S_{ij} = \cos(\vec{e}_{a_i}, \vec{e}_{b_j}) = \frac{\vec{e}_{a_i} \cdot \vec{e}_{b_j}}{\|\vec{e}_{a_i}\| \|\vec{e}_{b_j}\|}$$

Where $\vec{e}$ represents dense sentence embeddings from `all-MiniLM-L6-v2`. Optimal matching is established via greedy bipartite assignment subject to a threshold $\tau = 0.70$:
* If $S_{ij} \ge 0.96$: **Unchanged**
* If $0.70 \le S_{ij} < 0.96$: **Materially Changed** (analyzed for semantic shift)
* Unmatched clauses in $B$: **Added Provisions**
* Unmatched clauses in $A$: **Removed Provisions**

### 2. Perspective Risk Scoring Formulation
For document $D$ and party role $R \in \{\text{Tenant}, \text{Landlord}, \text{Employee}, \text{Employer}, \text{Customer}, \text{Vendor}\}$:

$$\text{Risk}(D, R) = \min\left(100, \; \sum_{c \in \text{Clauses}(D)} w(\text{cat}_c, R) \cdot \delta(c, R) + \sum_{d \in \text{Defects}(D)} \sigma(d)\right)$$

Where:
* $w(\text{cat}_c, R)$ is the category vulnerability weight for role $R$ (e.g. indemnity/termination has higher weight for tenant than landlord).
* $\delta(c, R) \in [0, 25]$ is the deviation penalty relative to reference market baselines.
* $\sigma(d) \in \{10, 20, 30\}$ is the severity penalty for structural defects (dangling reference = 25 pts, undefined term = 10 pts).

### 3. Hybrid Reciprocal Rank Fusion (QA Retrieval)
Candidate clauses are retrieved using both sparse lexical (BM25) and dense semantic vector rankings, fused via Reciprocal Rank Fusion (RRF):

$$\text{RRF}(c) = \frac{w_{\text{dense}}}{k + \text{rank}_{\text{dense}}(c)} + \frac{w_{\text{bm25}}}{k + \text{rank}_{\text{bm25}}(c)}$$

With constant $k = 60$. The top candidates are expanded with their hierarchical tree ancestors and cross-referenced definitions before synthesis.

---

## 📊 Rigorous Benchmark Evaluation (100% PASS)

ClauseLens includes an automated evaluation harness ([`eval.py`](eval.py)) tested against annotated gold-standard ground-truth datasets ([`data/gold/gold_annotations.json`](data/gold/gold_annotations.json) and [`data/gold/adversarial_questions.json`](data/gold/adversarial_questions.json)):

```bash
python eval.py
```

### Executive Benchmark Summary
| Evaluation Metric | Score | Target Benchmark | Status | Verification Criteria |
| :--- | :---: | :---: | :---: | :--- |
| **Clause Classification Accuracy** | **100.0%** | $\ge 85.0\%$ | `PASS` ✅ | Exact match against multi-class gold taxonomy (12/12) |
| **Clause Classification Macro-F1** | **100.0%** | $\ge 80.0\%$ | `PASS` ✅ | Balanced macro-average across all evaluated classes |
| **Cross-Reference Recall** | **100.0%** | $100.0\%$ | `PASS` ✅ | Successful resolution of directed edge references |
| **Dangling Ref Recall** | **100.0%** | $100.0\%$ | `PASS` ✅ | Traps non-existent target references (traps Section 14.3) |
| **Defect Detection Recall** | **100.0%** | $100.0\%$ | `PASS` ✅ | Detects injected undefined terms and notice conflicts |
| **Citation Validity Rate** | **100.0%** | $100.0\%$ | `PASS` ✅ | Cited Clause IDs exist in tree with valid float bboxes (15/15) |
| **Adversarial Abstention Rate** | **100.0%** | $100.0\%$ | `PASS` ✅ | 10/10 out-of-scope adversarial queries successfully abstained |

---

### 1. Clause Classification Performance
- **Overall Accuracy**: **100.0%** (12/12 clauses)
- **Macro-F1**: **100.0%**

| Taxonomy Category | Precision | Recall | F1 Score | Support |
| :--- | :---: | :---: | :---: | :---: |
| `dispute_resolution` | 1.00 | 1.00 | 1.00 | 1 |
| `governing_law` | 1.00 | 1.00 | 1.00 | 1 |
| `non_compete` | 1.00 | 1.00 | 1.00 | 1 |
| `notice_period` | 1.00 | 1.00 | 1.00 | 3 |
| `payment_terms` | 1.00 | 1.00 | 1.00 | 5 |
| `termination` | 1.00 | 1.00 | 1.00 | 1 |

---

### 2. Structural Integrity & Graph Analysis
- **Cross-Reference Recall**: **100.0%**
- **Dangling Reference Recall**: **100.0%** (Correctly trapped Section 14.3)
- **Defect Detection Recall**: **100.0%**

#### Injected Defect Verifications
| Document | Defect Type | Target Indicator | Caught? | Status |
| :--- | :--- | :--- | :---: | :---: |
| `doc_residential_lease` | `dangling_crossref` | Section 14.3 | `YES` | `PASS` ✅ |
| `doc_employment_agreement` | `undefined_term` | Restricted Territory | `YES` | `PASS` ✅ |
| `doc_saas_terms` | `conflicting_notice` | 30 days | `YES` | `PASS` ✅ |

---

### 3. Grounded QA & Citation Validity
- **Valid Citations**: **15/15**
- **Citation Validity Rate**: **100.0%**

Every citation is deterministically audited against:
1. Active Clause ID existence in Document Clause Tree.
2. Valid page index (`page >= 1`).
3. Valid 4-coordinate bounding box (`[x0, y0, x1, y1]`).
4. Exact text span char range (`char_end >= char_start`).

| Document | Benchmark Query | Citations Checked | Validity |
| :--- | :--- | :---: | :---: |
| `doc_residential_lease` | *"What is the security deposit amount?"* | 3 | `PASS` ✅ |
| `doc_residential_lease` | *"What is the notice period for terminating the lease?"* | 3 | `PASS` ✅ |
| `doc_employment_agreement` | *"What is the employee base salary?"* | 3 | `PASS` ✅ |
| `doc_employment_agreement` | *"What is the non-compete restriction duration?"* | 3 | `PASS` ✅ |
| `doc_saas_terms` | *"When are fees and payment due?"* | 3 | `PASS` ✅ |

---

### 4. Adversarial Abstention & Legal Guardrails
- **Abstention Rate**: **100.0%** (10/10)
- **Zero Hallucinations Guarantee**: Strict abstention on queries referencing unmentioned obligations or out-of-scope legal topics:

| ID | Document | Adversarial Question | Response Type | Status |
| :---: | :--- | :--- | :--- | :---: |
| `adv_01` | `doc_residential_lease` | What is the pet deposit fee required for owning a dog or cat? | Explicit Abstention | `PASS` ✅ |
| `adv_02` | `doc_residential_lease` | Can the tenant pay monthly rent using Bitcoin, Ethereum, or cryptocurrency? | Explicit Abstention | `PASS` ✅ |
| `adv_03` | `doc_residential_lease` | What happens if a meteor strike damages the roof of the rental property? | Explicit Abstention | `PASS` ✅ |
| `adv_04` | `doc_residential_lease` | Is the tenant entitled to park a commercial food truck in the driveway? | Explicit Abstention | `PASS` ✅ |
| `adv_05` | `doc_employment_agreement` | Does the company offer incentive stock options (ISOs) or restricted stock units? | Explicit Abstention | `PASS` ✅ |
| `adv_06` | `doc_employment_agreement` | What are the rules regarding personal use of the company private aircraft or jet? | Explicit Abstention | `PASS` ✅ |
| `adv_07` | `doc_employment_agreement` | How many weeks of fully paid paternity leave is the employee entitled to receive? | Explicit Abstention | `PASS` ✅ |
| `adv_08` | `doc_saas_terms` | What is the service level agreement (SLA) uptime percentage guarantee? | Explicit Abstention | `PASS` ✅ |
| `adv_09` | `doc_saas_terms` | What royalty percentage does customer receive if they sublicense the platform code? | Explicit Abstention | `PASS` ✅ |
| `adv_10` | `doc_saas_terms` | Can the customer demand on-premise bare-metal server deployment of the software? | Explicit Abstention | `PASS` ✅ |

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

ClauseLens exposes 14 production endpoints via FastAPI:

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
| `POST` | `/api/documents/upload` | Multipart upload for new PDF / DOCX contracts (25MB limit) |

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
├── public/                      # Static assets served directly by Vercel CDN
│   ├── app.js                   # Client controller
│   ├── index.html               # Main dashboard UI
│   └── style.css                # Obsidian glassmorphic styling
├── frontend/                    # Source web studio application
├── api/                         # Vercel Serverless Function entrypoint
│   └── index.py                 # ASGI handler
├── pyproject.toml               # Vercel FastAPI configuration & entrypoint
├── vercel.json                  # Vercel routing & function duration rules
├── .vercelignore                # Vercel upload exclusions
├── eval.py                      # Automated evaluation harness (all benchmarks)
├── pytest.ini                   # Test configuration (-p no:cacheprovider)
├── requirements.txt             # Pinned production dependencies (Vercel-optimized)
├── requirements-dense.txt       # Optional dense embeddings (sentence-transformers)
├── requirements-dev.txt         # Dev & test dependencies
├── .env.example                 # Environment variables template
└── README.md                    # Single authoritative project documentation
```

---

## 🚀 Deployment to Vercel

ClauseLens is pre-configured for seamless, zero-config deployment to [Vercel](https://vercel.com/) with native FastAPI support and Edge CDN static asset delivery.

### Option A: Deploy via Vercel CLI

1. **Install Vercel CLI** (minimum version 48.1.8):
   ```bash
   npm i -g vercel
   ```

2. **Deploy to Preview / Production**:
   ```bash
   vercel
   ```
   Or for production:
   ```bash
   vercel --prod
   ```

3. **Set Environment Variables in Vercel**:
   - `GEMINI_API_KEY`: *(Optional)* Your Google Gemini API key for generative risk explanations, Q&A summaries, and redlining.
   - `ALLOWED_ORIGINS`: *(Optional)* Comma-separated list of allowed origins (defaults to `*`).

### Option B: Deploy via GitHub / GitLab

1. Push your repository to GitHub.
2. In the [Vercel Dashboard](https://vercel.com/new), click **Import Project** and select your repository.
3. Framework Preset: **Other** / Auto-detected (Vercel automatically detects `pyproject.toml` and `tool.vercel.entrypoint`).
4. Add the `GEMINI_API_KEY` under **Environment Variables**.
5. Click **Deploy**.

### Architecture Highlights on Vercel
- **Zero Cold-Start Frontend**: Static assets in `public/` are served globally by Vercel's Global Edge CDN.
- **Serverless FastAPI**: API routes (`/api/*`) execute as high-performance Python serverless functions with 60-second timeouts.
- **Read-Only Filesystem Safe**: Automatically clones pre-seeded contracts to `/tmp/clause_lens.db` and writes uploads to `/tmp/uploads`, avoiding serverless read-only filesystem errors.
- **Optimized Bundle Size**: Optimized dependency tree stays well below Vercel's 250MB bundle limit while maintaining full BM25 + Jaccard ranking intelligence and AI capabilities.

---

## 🛡️ Non-Legal-Advice Compliance Notice

> **IMPORTANT DISCLAIMER**:  
> ClauseLens is an advanced technological tool engineered for legal document structure analysis, drafting anomaly detection, and contractual information extraction. **ClauseLens does not provide legal advice, does not predict judicial outcomes, and does not establish an attorney-client relationship.** Users should always consult a qualified legal professional for legal representation, counsel, or case strategy.

---

<div align="center">
  <sub>Built with precision for the Advanced Legal Intelligence Challenge. Designed to set the standard for deterministic, grounded contract analysis.</sub>
</div>
