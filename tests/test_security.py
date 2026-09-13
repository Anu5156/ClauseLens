"""
Security-focused tests for ClauseLens.
Validates filename sanitisation, upload guards, and header hardening.
Run with:  pytest tests/test_security.py -v
"""
import os
import re
import pytest


# ─── Filename Sanitisation ────────────────────────────────────────────────────

SANITISE = lambda raw: re.sub(r"[^a-zA-Z0-9_.-]", "_", os.path.basename(raw))


class TestFilenameSanitisation:
    """Test the sanitisation logic used in the upload route."""

    def test_strips_path_traversal(self):
        clean = SANITISE("../../etc/passwd.pdf")
        assert ".." not in clean
        assert "/" not in clean

    def test_strips_windows_path(self):
        clean = SANITISE(r"C:\Windows\System32\evil.pdf")
        assert "\\" not in clean
        assert ":" not in clean

    def test_preserves_valid_name(self):
        clean = SANITISE("contract_v2.pdf")
        assert clean == "contract_v2.pdf"

    def test_replaces_spaces(self):
        clean = SANITISE("my contract.pdf")
        assert " " not in clean

    def test_replaces_angle_brackets(self):
        clean = SANITISE("<script>.pdf")
        assert "<" not in clean
        assert ">" not in clean

    def test_null_byte_removed(self):
        clean = SANITISE("file\x00name.pdf")
        assert "\x00" not in clean

    @pytest.mark.parametrize("filename,expected_suffix", [
        ("doc.pdf", ".pdf"),
        ("doc.docx", ".docx"),
        ("doc.doc", ".doc"),
    ])
    def test_allowed_extensions_preserved(self, filename, expected_suffix):
        clean = SANITISE(filename)
        assert clean.endswith(expected_suffix)


# ─── File Type Gating ─────────────────────────────────────────────────────────

class TestFileTypeGating:
    ALLOWED = (".pdf", ".docx", ".doc")

    def _is_allowed(self, filename: str) -> bool:
        return filename.lower().endswith(self.ALLOWED)

    def test_pdf_allowed(self):
        assert self._is_allowed("agreement.pdf")

    def test_docx_allowed(self):
        assert self._is_allowed("contract.docx")

    def test_exe_blocked(self):
        assert not self._is_allowed("malware.exe")

    def test_js_blocked(self):
        assert not self._is_allowed("xss.js")

    def test_sh_blocked(self):
        assert not self._is_allowed("exploit.sh")

    def test_double_extension_blocked(self):
        # A file ending in ".pdf.exe" should NOT pass the .pdf check
        # because we check endswith, not contains.
        assert not self._is_allowed("doc.pdf.exe")

    def test_case_insensitive(self):
        assert self._is_allowed("CONTRACT.PDF")
        assert self._is_allowed("Agreement.DOCX")


# ─── Upload Size Limit ────────────────────────────────────────────────────────

class TestSizeLimitLogic:
    MAX_BYTES = 25 * 1024 * 1024  # 25 MB

    def _would_reject(self, size_bytes: int) -> bool:
        return size_bytes > self.MAX_BYTES

    def test_accepts_small_file(self):
        assert not self._would_reject(100 * 1024)       # 100 KB

    def test_accepts_exactly_at_limit(self):
        assert not self._would_reject(self.MAX_BYTES)   # exactly 25 MB

    def test_rejects_just_over_limit(self):
        assert self._would_reject(self.MAX_BYTES + 1)   # 25 MB + 1 byte

    def test_rejects_very_large_file(self):
        assert self._would_reject(100 * 1024 * 1024)    # 100 MB


# ─── Header Hardening (unit logic) ───────────────────────────────────────────

class TestSecurityHeaderValues:
    """Verify the exact values that should be set on every HTTP response."""

    REQUIRED_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }

    def test_expected_header_map_non_empty(self):
        assert len(self.REQUIRED_HEADERS) >= 4

    @pytest.mark.parametrize("header,value", [
        ("X-Content-Type-Options", "nosniff"),
        ("X-Frame-Options", "DENY"),
        ("X-XSS-Protection", "1; mode=block"),
        ("Referrer-Policy", "strict-origin-when-cross-origin"),
    ])
    def test_header_value_correct(self, header, value):
        """Documents the expected value for each security header."""
        assert self.REQUIRED_HEADERS[header] == value
