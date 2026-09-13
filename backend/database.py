import sqlite3
import json
from typing import Optional, List, Dict, Any
from backend.config import DATABASE_PATH
from backend.models import DocumentParsed, ClauseNode, CrossRefEdge, DefinedTerm, DefectItem, SpanLocation, RiskItem, DocumentRiskProfile

def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            file_type TEXT NOT NULL,
            doc_type TEXT DEFAULT 'unknown',
            upload_timestamp TEXT NOT NULL,
            page_count INTEGER NOT NULL,
            raw_text TEXT NOT NULL
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS clauses (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            clause_number TEXT NOT NULL,
            title TEXT NOT NULL,
            text TEXT NOT NULL,
            level INTEGER NOT NULL,
            category TEXT DEFAULT 'other',
            parent_id TEXT,
            children_json TEXT NOT NULL,
            spans_json TEXT NOT NULL,
            order_index INTEGER NOT NULL,
            FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS crossrefs (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            from_clause_id TEXT NOT NULL,
            from_clause_number TEXT NOT NULL,
            target_label TEXT NOT NULL,
            to_clause_id TEXT,
            reference_text TEXT NOT NULL,
            is_dangling INTEGER NOT NULL,
            FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS definitions (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            term TEXT NOT NULL,
            definition TEXT NOT NULL,
            clause_id TEXT NOT NULL,
            FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS defects (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            defect_type TEXT NOT NULL,
            description TEXT NOT NULL,
            clause_id TEXT,
            severity TEXT NOT NULL,
            FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS risk_items (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            clause_id TEXT NOT NULL,
            clause_number TEXT NOT NULL,
            category TEXT NOT NULL,
            deviation_rating TEXT NOT NULL,
            perspective_risk TEXT NOT NULL,
            rationale TEXT NOT NULL,
            driving_span TEXT NOT NULL,
            closest_reference_text TEXT NOT NULL,
            closest_reference_type TEXT NOT NULL,
            FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
        );
        """)

        # Migration check if existing database without new columns
        try:
            cursor.execute("ALTER TABLE documents ADD COLUMN doc_type TEXT DEFAULT 'unknown'")
        except Exception:
            pass

        try:
            cursor.execute("ALTER TABLE clauses ADD COLUMN category TEXT DEFAULT 'other'")
        except Exception:
            pass

        conn.commit()

def save_document(doc: DocumentParsed):
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM documents WHERE id = ?", (doc.id,))
        cursor.execute("DELETE FROM clauses WHERE document_id = ?", (doc.id,))
        cursor.execute("DELETE FROM crossrefs WHERE document_id = ?", (doc.id,))
        cursor.execute("DELETE FROM definitions WHERE document_id = ?", (doc.id,))
        cursor.execute("DELETE FROM defects WHERE document_id = ?", (doc.id,))

        cursor.execute(
            "INSERT INTO documents (id, filename, file_type, doc_type, upload_timestamp, page_count, raw_text) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (doc.id, doc.filename, doc.file_type, doc.doc_type, doc.upload_timestamp, doc.page_count, doc.raw_text)
        )

        for clause in doc.clauses:
            cursor.execute(
                """INSERT INTO clauses 
                   (id, document_id, clause_number, title, text, level, category, parent_id, children_json, spans_json, order_index)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    clause.id,
                    clause.document_id,
                    clause.clause_number,
                    clause.title,
                    clause.text,
                    clause.level,
                    clause.category,
                    clause.parent_id,
                    json.dumps(clause.children_ids),
                    json.dumps([s.model_dump() for s in clause.spans]),
                    clause.order_index
                )
            )

        for ref in doc.crossrefs:
            cursor.execute(
                """INSERT INTO crossrefs 
                   (id, document_id, from_clause_id, from_clause_number, target_label, to_clause_id, reference_text, is_dangling)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    ref.id,
                    ref.document_id,
                    ref.from_clause_id,
                    ref.from_clause_number,
                    ref.target_label,
                    ref.to_clause_id,
                    ref.reference_text,
                    1 if ref.is_dangling else 0
                )
            )

        for dterm in doc.definitions:
            cursor.execute(
                "INSERT INTO definitions (id, document_id, term, definition, clause_id) VALUES (?, ?, ?, ?, ?)",
                (dterm.id, dterm.document_id, dterm.term, dterm.definition, dterm.clause_id)
            )

        for defect in doc.defects:
            cursor.execute(
                "INSERT INTO defects (id, document_id, defect_type, description, clause_id, severity) VALUES (?, ?, ?, ?, ?, ?)",
                (defect.id, defect.document_id, defect.defect_type, defect.description, defect.clause_id, defect.severity)
            )
        conn.commit()

def get_document(doc_id: str) -> Optional[DocumentParsed]:
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        doc_row = cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
        if not doc_row:
            return None

        clause_rows = cursor.execute("SELECT * FROM clauses WHERE document_id = ? ORDER BY order_index ASC", (doc_id,)).fetchall()
        clauses = []
        for r in clause_rows:
            spans_raw = json.loads(r["spans_json"])
            spans = [SpanLocation(**s) for s in spans_raw]
            clauses.append(ClauseNode(
                id=r["id"],
                document_id=r["document_id"],
                clause_number=r["clause_number"],
                title=r["title"],
                text=r["text"],
                level=r["level"],
                category=r["category"] if "category" in r.keys() else "other",
                parent_id=r["parent_id"],
                children_ids=json.loads(r["children_json"]),
                spans=spans,
                order_index=r["order_index"]
            ))

        crossref_rows = cursor.execute("SELECT * FROM crossrefs WHERE document_id = ?", (doc_id,)).fetchall()
        crossrefs = [
            CrossRefEdge(
                id=r["id"],
                document_id=r["document_id"],
                from_clause_id=r["from_clause_id"],
                from_clause_number=r["from_clause_number"],
                target_label=r["target_label"],
                to_clause_id=r["to_clause_id"],
                reference_text=r["reference_text"],
                is_dangling=bool(r["is_dangling"])
            )
            for r in crossref_rows
        ]

        def_rows = cursor.execute("SELECT * FROM definitions WHERE document_id = ?", (doc_id,)).fetchall()
        definitions = [
            DefinedTerm(
                id=r["id"],
                document_id=r["document_id"],
                term=r["term"],
                definition=r["definition"],
                clause_id=r["clause_id"]
            )
            for r in def_rows
        ]

        defect_rows = cursor.execute("SELECT * FROM defects WHERE document_id = ?", (doc_id,)).fetchall()
        defects = [
            DefectItem(
                id=r["id"],
                document_id=r["document_id"],
                defect_type=r["defect_type"],
                description=r["description"],
                clause_id=r["clause_id"],
                severity=r["severity"]
            )
            for r in defect_rows
        ]

        doc_type_val = doc_row["doc_type"] if "doc_type" in doc_row.keys() else "unknown"

        return DocumentParsed(
            id=doc_row["id"],
            filename=doc_row["filename"],
            file_type=doc_row["file_type"],
            doc_type=doc_type_val,
            upload_timestamp=doc_row["upload_timestamp"],
            page_count=doc_row["page_count"],
            raw_text=doc_row["raw_text"],
            clauses=clauses,
            crossrefs=crossrefs,
            definitions=definitions,
            defects=defects
        )

def list_documents() -> List[Dict[str, Any]]:
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        rows = cursor.execute("SELECT id, filename, file_type, doc_type, upload_timestamp, page_count FROM documents").fetchall()
        return [dict(r) for r in rows]
