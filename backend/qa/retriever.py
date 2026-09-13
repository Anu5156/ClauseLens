import re
import math
from typing import List, Tuple, Dict
from rank_bm25 import BM25Okapi
from backend.models import ClauseNode

_embedding_model = None

def get_dense_model():
    """Lazily load sentence-transformers model if available."""
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception:
            _embedding_model = False
    return _embedding_model if _embedding_model is not False else None

def tokenize(text: str) -> List[str]:
    clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', text.lower())
    return [w for w in clean.split() if len(w) > 1]

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

def hybrid_retrieve_clauses(
    query: str,
    clauses: List[ClauseNode],
    top_k: int = 5,
    rrf_k: int = 60
) -> List[Tuple[ClauseNode, float]]:
    """
    Hybrid retrieval using BM25 lexical search + dense embedding search fused with RRF.
    Returns list of (ClauseNode, fused_score).
    """
    if not clauses:
        return []

    # 1. Lexical Retrieval (BM25)
    tokenized_corpus = [tokenize(f"{c.title} {c.text}") for c in clauses]
    tokenized_query = tokenize(query)
    
    bm25 = BM25Okapi(tokenized_corpus)
    bm25_scores = bm25.get_scores(tokenized_query) if tokenized_query else [0.0] * len(clauses)
    
    # Rank by BM25 descending
    bm25_ranked_indices = sorted(range(len(clauses)), key=lambda i: bm25_scores[i], reverse=True)
    bm25_rank_map = {idx: rank + 1 for rank, idx in enumerate(bm25_ranked_indices)}

    # 2. Dense Vector Retrieval
    dense_model = get_dense_model()
    if dense_model:
        clause_texts = [f"{c.title}: {c.text}" for c in clauses]
        doc_embeddings = dense_model.encode(clause_texts, convert_to_numpy=True)
        query_embedding = dense_model.encode([query], convert_to_numpy=True)[0]
        
        import numpy as np
        # Compute cosine similarities
        norms_doc = np.linalg.norm(doc_embeddings, axis=1)
        norm_q = np.linalg.norm(query_embedding)
        if norm_q > 0:
            dense_scores = np.dot(doc_embeddings, query_embedding) / (norms_doc * norm_q + 1e-9)
        else:
            dense_scores = np.zeros(len(clauses))
        
        dense_ranked_indices = np.argsort(-dense_scores)
        dense_rank_map = {int(idx): rank + 1 for rank, idx in enumerate(dense_ranked_indices)}
    else:
        # Fallback: lexical Jaccard/overlap ranking as second ranker
        query_set = set(tokenized_query)
        overlap_scores = [
            len(query_set.intersection(set(corp))) / (len(query_set.union(set(corp))) + 1e-9)
            for corp in tokenized_corpus
        ]
        dense_ranked_indices = sorted(range(len(clauses)), key=lambda i: overlap_scores[i], reverse=True)
        dense_rank_map = {idx: rank + 1 for rank, idx in enumerate(dense_ranked_indices)}

    # 3. Reciprocal Rank Fusion (RRF)
    rrf_scores: Dict[int, float] = {}
    for i in range(len(clauses)):
        rank_bm25 = bm25_rank_map[i]
        rank_dense = dense_rank_map[i]
        rrf = (1.0 / (rrf_k + rank_bm25)) + (1.0 / (rrf_k + rank_dense))
        
        # If BM25 had 0 match and dense/overlap had 0 match, penalize
        if max(bm25_scores[i], 0) == 0:
            rrf *= 0.5
            
        rrf_scores[i] = rrf

    # Sort all by RRF score descending
    sorted_indices = sorted(rrf_scores.keys(), key=lambda i: rrf_scores[i], reverse=True)
    
    results = [(clauses[i], rrf_scores[i]) for i in sorted_indices[:top_k]]
    return results
