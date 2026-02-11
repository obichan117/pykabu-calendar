"""Tests for IR URL patterns module."""

import pytest
import requests

from pykabu_calendar.earnings.ir import get_candidate_urls, IR_PATH_PATTERNS, CALENDAR_PATH_PATTERNS
from pykabu_calendar.earnings.ir.patterns import normalize_base_url


class TestNormalizeBaseUrl:
    """Tests for normalize_base_url function."""

    def test_simple_url(self):
        """Test normalizing a simple URL."""
        result = normalize_base_url("https://www.example.co.jp/")
        assert result == "https://www.example.co.jp"

    def test_url_with_path(self):
        """Test normalizing URL with path."""
        result = normalize_base_url("https://www.example.co.jp/about/company/")
        assert result == "https://www.example.co.jp"

    def test_url_without_scheme(self):
        """Test normalizing URL without scheme."""
        result = normalize_base_url("www.example.co.jp")
        assert result == "https://www.example.co.jp"

    def test_http_url(self):
        """Test preserving http scheme."""
        result = normalize_base_url("http://www.example.co.jp/")
        assert result == "http://www.example.co.jp"

    def test_empty_url(self):
        """Test handling empty URL."""
        assert normalize_base_url("") == ""
        assert normalize_base_url(None) == ""


class TestGetCandidateUrls:
    """Tests for get_candidate_urls function."""

    def test_generates_urls(self):
        """Test that candidate URLs are generated."""
        urls = get_candidate_urls("https://www.example.co.jp/")
        assert len(urls) > 0
        assert all(url.startswith("https://www.example.co.jp") for url in urls)

    def test_includes_ir_paths(self):
        """Test that IR paths are included."""
        urls = get_candidate_urls("https://www.example.co.jp/")
        assert "https://www.example.co.jp/ir/" in urls

    def test_includes_calendar_paths(self):
        """Test that calendar paths are included."""
        urls = get_candidate_urls("https://www.example.co.jp/")
        assert "https://www.example.co.jp/ir/calendar/" in urls

    def test_no_duplicates(self):
        """Test that there are no duplicate URLs."""
        urls = get_candidate_urls("https://www.example.co.jp/")
        assert len(urls) == len(set(urls))

    def test_calendar_only(self):
        """Test getting only calendar URLs."""
        urls = get_candidate_urls(
            "https://www.example.co.jp/",
            include_calendar=True,
            include_ir_landing=False,
        )
        # Should not include basic /ir/ path
        assert "https://www.example.co.jp/ir/" not in urls
        # Should include calendar paths
        assert "https://www.example.co.jp/ir/calendar/" in urls

    def test_ir_landing_only(self):
        """Test getting only IR landing URLs."""
        urls = get_candidate_urls(
            "https://www.example.co.jp/",
            include_calendar=False,
            include_ir_landing=True,
        )
        # Should include basic /ir/ path
        assert "https://www.example.co.jp/ir/" in urls
        # Should not include calendar paths
        assert "https://www.example.co.jp/ir/calendar/" not in urls

    def test_preserves_original_path(self):
        """Test that URLs based on original path are included."""
        urls = get_candidate_urls("https://www.example.co.jp/company/jp/")
        # Should include path-based IR URL
        assert "https://www.example.co.jp/company/jp/ir/" in urls

    def test_empty_url(self):
        """Test handling empty URL."""
        assert get_candidate_urls("") == []
        assert get_candidate_urls(None) == []


class TestPatternConstants:
    """Tests for pattern constants."""

    def test_ir_patterns_not_empty(self):
        """Test that IR patterns list is not empty."""
        assert len(IR_PATH_PATTERNS) > 0

    def test_calendar_patterns_not_empty(self):
        """Test that calendar patterns list is not empty."""
        assert len(CALENDAR_PATH_PATTERNS) > 0

    def test_patterns_are_paths(self):
        """Test that patterns start with /."""
        for pattern in IR_PATH_PATTERNS:
            assert pattern.startswith("/"), f"Pattern should start with /: {pattern}"
        for pattern in CALENDAR_PATH_PATTERNS:
            assert pattern.startswith("/"), f"Pattern should start with /: {pattern}"


class TestRealCompanyUrls:
    """Integration tests with real company websites."""

    # Known company IR pages for validation
    KNOWN_IR_PAGES = {
        "7203": {  # Toyota
            "website": "https://global.toyota/jp/",
            "ir_url": "https://global.toyota/jp/ir/",
        },
        "6758": {  # Sony
            "website": "https://www.sony.com/ja/",
            "ir_url": "https://www.sony.com/ja/SonyInfo/IR/",
        },
        "9984": {  # SoftBank Group
            "website": "https://group.softbank/",
            "ir_url": "https://group.softbank/ir/",
        },
        "8306": {  # MUFG
            "website": "https://www.mufg.jp/",
            "ir_url": "https://www.mufg.jp/ir/",
        },
        "7267": {  # Honda
            "website": "https://www.honda.co.jp/",
            "ir_url": "https://www.honda.co.jp/investors/",
        },
        "9432": {  # NTT
            "website": "https://group.ntt/jp/",
            "ir_url": "https://group.ntt/jp/ir/",
        },
        "8035": {  # Tokyo Electron
            "website": "https://www.tel.co.jp/",
            "ir_url": "https://www.tel.co.jp/ir/",
        },
        "2802": {  # Ajinomoto
            "website": "https://www.ajinomoto.co.jp/company/jp/aboutus/",
            "ir_url": "https://www.ajinomoto.co.jp/company/jp/ir/",
        },
        "6501": {  # Hitachi
            "website": "https://www.hitachi.com/ja-jp/",
            "ir_url": "https://www.hitachi.co.jp/IR/",
        },
        "4502": {  # Takeda
            "website": "https://www.takeda.com/jp/",
            "ir_url": "https://www.takeda.com/jp/investors/",
        },
    }

    def test_candidate_urls_generated(self):
        """Test that candidate URLs are generated for all known companies."""
        for code, data in self.KNOWN_IR_PAGES.items():
            urls = get_candidate_urls(data["website"])
            assert len(urls) > 5, f"Should generate multiple candidates for {code}"

    @pytest.mark.slow
    def test_known_ir_pages_accessible(self):
        """Test that known IR pages are actually accessible."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        for code, data in self.KNOWN_IR_PAGES.items():
            try:
                response = requests.head(
                    data["ir_url"],
                    headers=headers,
                    timeout=10,
                    allow_redirects=True,
                )
                # Accept 200, 301, 302, 403 (some block HEAD requests)
                assert response.status_code in [
                    200,
                    301,
                    302,
                    403,
                ], f"IR page for {code} returned {response.status_code}"
            except requests.RequestException as e:
                pytest.skip(f"Network error checking {code}: {e}")
