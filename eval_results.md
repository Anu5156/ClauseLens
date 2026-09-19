# ClauseLens Benchmark Evaluation Report (Phase 7)

**Timestamp**: 2026-09-19 09:52:12  
**Evaluation Harness**: `eval.py`  
**Status**: ALL PASSING

## Executive Summary

| Evaluation Metric | Score | Target Benchmark | Status |
| :--- | :---: | :---: | :---: |
| Clause Classification Accuracy | **100.0%** | >= 85.0% | `PASS` |
| Clause Classification Macro-F1 | **100.0%** | >= 80.0% | `PASS` |
| Cross-Reference Recall | **100.0%** | 100.0% | `PASS` |
| Dangling Ref Recall | **100.0%** | 100.0% | `PASS` |
| Defect Detection Recall | **100.0%** | 100.0% | `PASS` |
| Citation Validity Rate | **100.0%** | 100.0% | `PASS` |
| Adversarial Abstention Rate | **100.0%** | 100.0% | `PASS` |

---

## 1. Clause Classification Performance
- **Overall Accuracy**: 100.0% (12/12 clauses)
- **Macro-F1**: 100.0%

| Taxonomy Category | Precision | Recall | F1 Score | Support |
| :--- | :---: | :---: | :---: | :---: |
| `dispute_resolution` | 1.00 | 1.00 | 1.00 | 1 |
| `governing_law` | 1.00 | 1.00 | 1.00 | 1 |
| `non_compete` | 1.00 | 1.00 | 1.00 | 1 |
| `notice_period` | 1.00 | 1.00 | 1.00 | 3 |
| `payment_terms` | 1.00 | 1.00 | 1.00 | 5 |
| `termination` | 1.00 | 1.00 | 1.00 | 1 |

---

## 2. Structural Integrity & Graph Analysis
- **Cross-Reference Recall**: 100.0%
- **Dangling Reference Recall**: 100.0% (Correctly trapped Section 14.3)
- **Defect Detection Recall**: 100.0%

### Injected Defect Verifications
| Document | Defect Type | Target Indicator | Caught? |
| :--- | :--- | :--- | :---: |
| `doc_residential_lease` | `dangling_crossref` | Section 14.3 | `PASS` |
| `doc_employment_agreement` | `undefined_term` | Restricted Territory | `PASS` |
| `doc_saas_terms` | `conflicting_notice` | 30 days | `PASS` |

---

## 3. Grounded QA & Citation Validity
- **Valid Citations**: 15/15
- **Citation Validity Rate**: 100.0%

Every citation verified against:
1. Active Clause ID existence in Document Clause Tree.
2. Valid page index (`page >= 1`).
3. Valid 4-coordinate bounding box (`[x0, y0, x1, y1]`).
4. Exact text span char range (`char_end >= char_start`).

| Document | Benchmark Query | Citations Checked | Validity |
| :--- | :--- | :---: | :---: |
| `doc_residential_lease` | "What is the security deposit amount?" | 3 | `PASS` |
| `doc_residential_lease` | "What is the notice period for terminating the lease?" | 3 | `PASS` |
| `doc_employment_agreement` | "What is the employee base salary?" | 3 | `PASS` |
| `doc_employment_agreement` | "What is the non-compete restriction duration?" | 3 | `PASS` |
| `doc_saas_terms` | "When are fees and payment due?" | 3 | `PASS` |

---

## 4. Adversarial Abstention & Legal Guardrails
- **Abstention Rate**: 100.0% (10/10)

Evaluated on 10 out-of-scope adversarial questions targeting non-existent contract clauses (cryptocurrency payments, private jets, pet deposits, equity ISOs, meteor strikes):

| ID | Document | Adversarial Question | Response Type | Status |
| :---: | :--- | :--- | :--- | :---: |
| `adv_01` | `doc_residential_lease` | What is the pet deposit fee required for owning a dog or cat? | Explicit Abstention | `PASS` |
| `adv_02` | `doc_residential_lease` | Can the tenant pay monthly rent using Bitcoin, Ethereum, or cryptocurrency? | Explicit Abstention | `PASS` |
| `adv_03` | `doc_residential_lease` | What happens if a meteor strike damages the roof of the rental property? | Explicit Abstention | `PASS` |
| `adv_04` | `doc_residential_lease` | Is the tenant entitled to park a commercial food truck in the driveway? | Explicit Abstention | `PASS` |
| `adv_05` | `doc_employment_agreement` | Does the company offer incentive stock options (ISOs) or restricted stock units? | Explicit Abstention | `PASS` |
| `adv_06` | `doc_employment_agreement` | What are the rules regarding personal use of the company private aircraft or jet? | Explicit Abstention | `PASS` |
| `adv_07` | `doc_employment_agreement` | How many weeks of fully paid paternity leave is the employee entitled to receive? | Explicit Abstention | `PASS` |
| `adv_08` | `doc_saas_terms` | What is the service level agreement (SLA) uptime percentage guarantee? | Explicit Abstention | `PASS` |
| `adv_09` | `doc_saas_terms` | What royalty percentage does customer receive if they sublicense the platform code? | Explicit Abstention | `PASS` |
| `adv_10` | `doc_saas_terms` | Can the customer demand on-premise bare-metal server deployment of the software? | Explicit Abstention | `PASS` |
