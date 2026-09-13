import re
import numpy as np
from typing import List, Dict, Tuple, Set, Optional
from backend.models import ClauseNode, DocumentParsed, ClauseComparisonItem, DocumentComparisonResult
from backend.qa.retriever import get_dense_model, tokenize
from backend.comparison.summarizer import summarize_semantic_change

def compute_clause_similarity_matrix(
    clauses_a: List[ClauseNode],
    clauses_b: List[ClauseNode]
) -> np.ndarray:
    """
    Computes a pairwise similarity matrix between clauses_a and clauses_b
    incorporating dense embeddings, taxonomy category matching, and clause numbering.
    """
    len_a = len(clauses_a)
    len_b = len(clauses_b)
    if len_a == 0 or len_b == 0:
        return np.zeros((len_a, len_b))

    matrix = np.zeros((len_a, len_b))

    # 1. Dense Embedding Similarities
    dense_model = get_dense_model()
    if dense_model:
        texts_a = [f"{c.title}: {c.text}" for c in clauses_a]
        texts_b = [f"{c.title}: {c.text}" for c in clauses_b]
        emb_a = dense_model.encode(texts_a, convert_to_numpy=True)
        emb_b = dense_model.encode(texts_b, convert_to_numpy=True)

        norm_a = np.linalg.norm(emb_a, axis=1, keepdims=True)
        norm_b = np.linalg.norm(emb_b, axis=1, keepdims=True)
        dense_sim = np.dot(emb_a, emb_b.T) / (np.dot(norm_a, norm_b.T) + 1e-9)
    else:
        # Token overlap fallback
        dense_sim = np.zeros((len_a, len_b))
        for i, ca in enumerate(clauses_a):
            toks_a = set(tokenize(f"{ca.title} {ca.text}"))
            for j, cb in enumerate(clauses_b):
                toks_b = set(tokenize(f"{cb.title} {cb.text}"))
                union_len = len(toks_a.union(toks_b))
                if union_len > 0:
                    dense_sim[i, j] = len(toks_a.intersection(toks_b)) / union_len

    # 2. Add Category and Numbering Bonuses
    for i, ca in enumerate(clauses_a):
        cat_a = getattr(ca, "category", "other")
        num_a = ca.clause_number.strip().lower()
        title_a = ca.title.strip().lower()

        for j, cb in enumerate(clauses_b):
            cat_b = getattr(cb, "category", "other")
            num_b = cb.clause_number.strip().lower()
            title_b = cb.title.strip().lower()

            score = dense_sim[i, j] * 0.65

            # Category match bonus
            if cat_a != "other" and cat_a == cat_b:
                score += 0.20

            # Exact number match bonus
            if num_a and num_a == num_b:
                score += 0.15
            elif num_a and num_b and (num_a in num_b or num_b in num_a):
                score += 0.08

            # Title match bonus
            if title_a and title_b and title_a == title_b:
                score += 0.10

            matrix[i, j] = min(1.0, score)

    return matrix

def compare_documents(
    doc_a: DocumentParsed,
    doc_b: DocumentParsed,
    alignment_threshold: float = 0.55
) -> DocumentComparisonResult:
    """
    Aligns clauses between doc_a (baseline) and doc_b (revision) using greedy matching,
    and categorizes differences into: added, removed, materially_changed, and unchanged.
    """
    clauses_a = doc_a.clauses
    clauses_b = doc_b.clauses

    sim_matrix = compute_clause_similarity_matrix(clauses_a, clauses_b)

    # Greedy bipartite matching
    pairs = []
    for i in range(len(clauses_a)):
        for j in range(len(clauses_b)):
            pairs.append((sim_matrix[i, j], i, j))

    pairs.sort(key=lambda x: x[0], reverse=True)

    matched_a: Set[int] = set()
    matched_b: Set[int] = set()
    aligned_pairs: List[Tuple[int, int, float]] = []

    for score, i, j in pairs:
        if score < alignment_threshold:
            break
        if i not in matched_a and j not in matched_b:
            matched_a.add(i)
            matched_b.add(j)
            aligned_pairs.append((i, j, float(score)))

    added_items: List[ClauseComparisonItem] = []
    removed_items: List[ClauseComparisonItem] = []
    changed_items: List[ClauseComparisonItem] = []
    unchanged_items: List[ClauseComparisonItem] = []

    # 1. Process Matched Pairs
    for i, j, score in aligned_pairs:
        ca = clauses_a[i]
        cb = clauses_b[j]

        clean_text_a = " ".join(ca.text.split())
        clean_text_b = " ".join(cb.text.split())

        cat = getattr(cb, "category", getattr(ca, "category", "other"))

        if clean_text_a == clean_text_b:
            unchanged_items.append(ClauseComparisonItem(
                clause_id_a=ca.id,
                clause_number_a=ca.clause_number,
                title_a=ca.title,
                text_a=ca.text,
                clause_id_b=cb.id,
                clause_number_b=cb.clause_number,
                title_b=cb.title,
                text_b=cb.text,
                category=cat,
                status="unchanged",
                similarity_score=round(score, 3),
                semantic_change_summary="No substantive change in text or provisions."
            ))
        else:
            summary = summarize_semantic_change(ca, cb)
            changed_items.append(ClauseComparisonItem(
                clause_id_a=ca.id,
                clause_number_a=ca.clause_number,
                title_a=ca.title,
                text_a=ca.text,
                clause_id_b=cb.id,
                clause_number_b=cb.clause_number,
                title_b=cb.title,
                text_b=cb.text,
                category=cat,
                status="materially_changed",
                similarity_score=round(score, 3),
                semantic_change_summary=summary
            ))

    # 2. Process Removed Clauses (in A but not in B)
    for i, ca in enumerate(clauses_a):
        if i not in matched_a:
            removed_items.append(ClauseComparisonItem(
                clause_id_a=ca.id,
                clause_number_a=ca.clause_number,
                title_a=ca.title,
                text_a=ca.text,
                category=getattr(ca, "category", "other"),
                status="removed",
                similarity_score=0.0,
                semantic_change_summary=f"Clause {ca.clause_number} ({ca.title}) was completely omitted/removed in revision."
            ))

    # 3. Process Added Clauses (in B but not in A)
    for j, cb in enumerate(clauses_b):
        if j not in matched_b:
            added_items.append(ClauseComparisonItem(
                clause_id_b=cb.id,
                clause_number_b=cb.clause_number,
                title_b=cb.title,
                text_b=cb.text,
                category=getattr(cb, "category", "other"),
                status="added",
                similarity_score=0.0,
                semantic_change_summary=f"Newly added clause {cb.clause_number} ({cb.title}) introducing new rights or obligations."
            ))

    # Sort results by clause ordering
    changed_items.sort(key=lambda x: x.clause_number_b or "")
    added_items.sort(key=lambda x: x.clause_number_b or "")
    removed_items.sort(key=lambda x: x.clause_number_a or "")
    unchanged_items.sort(key=lambda x: x.clause_number_b or "")

    summary_stats = {
        "total_clauses_doc_a": len(clauses_a),
        "total_clauses_doc_b": len(clauses_b),
        "added_count": len(added_items),
        "removed_count": len(removed_items),
        "materially_changed_count": len(changed_items),
        "unchanged_count": len(unchanged_items)
    }

    return DocumentComparisonResult(
        doc_id_a=doc_a.id,
        doc_id_b=doc_b.id,
        added=added_items,
        removed=removed_items,
        materially_changed=changed_items,
        unchanged=unchanged_items,
        summary_stats=summary_stats
    )
