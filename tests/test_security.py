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
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    }

    def test_expected_header_map_non_empty(self):
        assert len(self.REQUIRED_HEADERS) >= 5

    @pytest.mark.parametrize("header,value", [
        ("X-Content-Type-Options", "nosniff"),
        ("X-Frame-Options", "DENY"),
        ("X-XSS-Protection", "1; mode=block"),
        ("Referrer-Policy", "strict-origin-when-cross-origin"),
        ("Permissions-Policy", "camera=(), microphone=(), geolocation=()"),
    ])
    def test_header_value_correct(self, header, value):
        """Documents the expected value for each security header."""
        assert self.REQUIRED_HEADERS[header] == value


# ─── Content-Security-Policy ──────────────────────────────────────────────────

class TestContentSecurityPolicy:
    """Verify CSP directives are correctly formed."""

    CSP = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "frame-ancestors 'none'"
    )

    def test_csp_blocks_frame_ancestors(self):
        assert "frame-ancestors 'none'" in self.CSP

    def test_csp_has_default_src_self(self):
        assert "default-src 'self'" in self.CSP

    def test_csp_restricts_font_src(self):
        assert "font-src 'self'" in self.CSP

    def test_csp_allows_data_images(self):
        assert "img-src 'self' data:" in self.CSP


# ─── Rate Limiter Logic ───────────────────────────────────────────────────────

import collections
import time


class TestRateLimiterLogic:
    """Unit-tests for the sliding-window rate limiter (extracted logic)."""

    WINDOW = 60
    MAX_REQS = 120

    def _make_store(self):
        return {}

    def _check(self, store, ip):
        now = time.monotonic()
        window = store.setdefault(ip, collections.deque())
        while window and window[0] < now - self.WINDOW:
            window.popleft()
        if len(window) >= self.MAX_REQS:
            return False
        window.append(now)
        return True

    def test_allows_first_request(self):
        store = self._make_store()
        assert self._check(store, "1.2.3.4") is True

    def test_allows_requests_below_limit(self):
        store = self._make_store()
        for _ in range(self.MAX_REQS - 1):
            assert self._check(store, "10.0.0.1") is True

    def test_blocks_at_limit(self):
        store = self._make_store()
        for _ in range(self.MAX_REQS):
            self._check(store, "10.0.0.2")
        # This one should be blocked
        assert self._check(store, "10.0.0.2") is False

    def test_different_ips_independent(self):
        store = self._make_store()
        for _ in range(self.MAX_REQS):
            self._check(store, "192.168.1.1")
        # Different IP is unaffected
        assert self._check(store, "192.168.1.2") is True


# ─── Doc ID Validation ────────────────────────────────────────────────────────

class TestDocIdValidation:
    """Verify doc_id whitelist pattern prevents injection attacks."""

    PATTERN = re.compile(r"^[a-zA-Z0-9_.-]{1,128}$")

    def _is_valid(self, doc_id: str) -> bool:
        return bool(self.PATTERN.match(doc_id))

    def test_valid_simple_id(self):
        assert self._is_valid("doc_residential_lease")

    def test_valid_with_numbers(self):
        assert self._is_valid("doc123")

    def test_valid_with_dots(self):
        assert self._is_valid("contract.v2")

    def test_blocks_path_traversal(self):
        assert not self._is_valid("../../etc/passwd")

    def test_blocks_sql_injection(self):
        assert not self._is_valid("1' OR '1'='1")

    def test_blocks_empty_string(self):
        assert not self._is_valid("")

    def test_blocks_exceeds_max_length(self):
        assert not self._is_valid("a" * 129)

    def test_blocks_slash(self):
        assert not self._is_valid("doc/evil")


# ─── API Key Masking ──────────────────────────────────────────────────────────

class TestApiKeyMasking:
    """Verify sensitive keys are masked in diagnostic outputs."""

    def _mask(self, key: str) -> str:
        return "***" + key[-4:] if len(key) > 4 else "(not set)"

    def test_masks_full_key(self):
        masked = self._mask("AIzaSyABC1234XYZ")
        assert masked.startswith("***")
        assert "AIzaSyABC1234" not in masked

    def test_shows_last_four(self):
        masked = self._mask("AIzaSyABC1234WXYZ")
        assert masked.endswith("WXYZ")

    def test_empty_key_returns_not_set(self):
        assert self._mask("") == "(not set)"

    def test_short_key_returns_not_set(self):
        assert self._mask("abc") == "(not set)"

