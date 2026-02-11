"""Tests for IR page discovery module."""

import pytest
from unittest.mock import Mock, patch

from pykabu_calendar.earnings.ir import (
    IRPageInfo,
    IRPageType,
    discover_ir_page,
)
from pykabu_calendar.earnings.ir.discovery import (
    _check_url_exists,
    _detect_page_type,
    _find_ir_link_in_html,
)


class TestIRPageInfo:
    """Tests for IRPageInfo dataclass."""

    def test_basic_creation(self):
        """Test creating an IRPageInfo."""
        info = IRPageInfo(
            url="https://example.com/ir/",
            page_type=IRPageType.LANDING,
            company_code="1234",
        )
        assert info.url == "https://example.com/ir/"
        assert info.page_type == IRPageType.LANDING
        assert info.company_code == "1234"
        assert info.company_name is None
        assert info.discovered_via == "pattern"

    def test_with_all_fields(self):
        """Test creating with all fields."""
        info = IRPageInfo(
            url="https://example.com/ir/calendar/",
            page_type=IRPageType.CALENDAR,
            company_code="7203",
            company_name="Toyota",
            discovered_via="llm",
        )
        assert info.company_name == "Toyota"
        assert info.discovered_via == "llm"

    def test_str_representation(self):
        """Test string representation."""
        info = IRPageInfo(
            url="https://example.com/ir/",
            page_type=IRPageType.LANDING,
            company_code="1234",
        )
        str_repr = str(info)
        assert "1234" in str_repr
        assert "landing" in str_repr


class TestIRPageType:
    """Tests for IRPageType enum."""

    def test_all_types(self):
        """Test all page types exist."""
        assert IRPageType.CALENDAR.value == "calendar"
        assert IRPageType.NEWS.value == "news"
        assert IRPageType.LIBRARY.value == "library"
        assert IRPageType.LANDING.value == "landing"
        assert IRPageType.UNKNOWN.value == "unknown"


class TestDetectPageType:
    """Tests for _detect_page_type function."""

    def test_calendar_url(self):
        """Test detecting calendar page from URL."""
        assert _detect_page_type("https://example.com/ir/calendar/") == IRPageType.CALENDAR
        assert _detect_page_type("https://example.com/ir/schedule.html") == IRPageType.CALENDAR
        assert _detect_page_type("https://example.com/ir/event/") == IRPageType.CALENDAR

    def test_news_url(self):
        """Test detecting news page from URL."""
        assert _detect_page_type("https://example.com/ir/news/") == IRPageType.NEWS
        assert _detect_page_type("https://example.com/ir/release/") == IRPageType.NEWS

    def test_library_url(self):
        """Test detecting library page from URL."""
        assert _detect_page_type("https://example.com/ir/library/") == IRPageType.LIBRARY

    def test_landing_url(self):
        """Test detecting landing page from URL."""
        assert _detect_page_type("https://example.com/ir/") == IRPageType.LANDING
        assert _detect_page_type("https://example.com/investor/") == IRPageType.LANDING

    def test_unknown_url(self):
        """Test unknown page type."""
        assert _detect_page_type("https://example.com/about/") == IRPageType.UNKNOWN

    def test_with_html_content(self):
        """Test detecting from HTML content."""
        html = "<html><body><h1>決算カレンダー</h1></body></html>"
        assert _detect_page_type("https://example.com/page/", html) == IRPageType.CALENDAR


class TestFindIrLinkInHtml:
    """Tests for _find_ir_link_in_html function."""

    def test_finds_ir_link_by_text(self):
        """Test finding IR link by text content."""
        html = """
        <html><body>
            <a href="/about/">About Us</a>
            <a href="/ir/">IR情報</a>
            <a href="/contact/">Contact</a>
        </body></html>
        """
        result = _find_ir_link_in_html(html, "https://example.com/")
        assert result == "https://example.com/ir/"

    def test_finds_ir_link_by_href(self):
        """Test finding IR link by href pattern."""
        html = """
        <html><body>
            <a href="/about/">About</a>
            <a href="/investor/">Investor</a>
        </body></html>
        """
        result = _find_ir_link_in_html(html, "https://example.com/")
        assert result == "https://example.com/investor/"

    def test_resolves_relative_url(self):
        """Test resolving relative URLs."""
        html = '<a href="../ir/index.html">IR</a>'
        result = _find_ir_link_in_html(html, "https://example.com/company/")
        assert result == "https://example.com/ir/index.html"

    def test_no_ir_link(self):
        """Test when no IR link exists."""
        html = '<a href="/about/">About</a>'
        result = _find_ir_link_in_html(html, "https://example.com/")
        assert result is None


class TestCheckUrlExists:
    """Tests for _check_url_exists function."""

    @patch("pykabu_calendar.earnings.ir.discovery.get_session")
    def test_url_exists(self, mock_get_session):
        """Test checking existing URL."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.url = "https://example.com/ir/"
        mock_session.head.return_value = mock_response
        mock_get_session.return_value = mock_session

        exists, final_url = _check_url_exists("https://example.com/ir/")
        assert exists is True
        assert final_url == "https://example.com/ir/"

    @patch("pykabu_calendar.earnings.ir.discovery.get_session")
    def test_url_not_found(self, mock_get_session):
        """Test checking non-existent URL."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 404
        mock_session.head.return_value = mock_response
        mock_get_session.return_value = mock_session

        exists, final_url = _check_url_exists("https://example.com/missing/")
        assert exists is False
        assert final_url is None

    @patch("pykabu_calendar.earnings.ir.discovery.get_session")
    def test_fallback_to_get(self, mock_get_session):
        """Test fallback to GET when HEAD returns 403."""
        mock_session = Mock()
        mock_head_response = Mock()
        mock_head_response.status_code = 403
        mock_session.head.return_value = mock_head_response

        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.url = "https://example.com/ir/"
        mock_session.get.return_value = mock_get_response
        mock_get_session.return_value = mock_session

        exists, final_url = _check_url_exists("https://example.com/ir/")
        assert exists is True


class TestDiscoverIrPage:
    """Tests for discover_ir_page function."""

    @patch("pykabu_calendar.earnings.ir.discovery.Ticker")
    @patch("pykabu_calendar.earnings.ir.discovery._check_url_exists")
    def test_discovers_via_pattern(self, mock_check, mock_ticker):
        """Test discovering IR page via URL pattern."""
        # Setup mock ticker
        mock_profile = Mock()
        mock_profile.website = "https://example.com/"
        mock_profile.name = "Example Corp"
        mock_ticker.return_value.profile = mock_profile

        # First candidate URL succeeds
        mock_check.return_value = (True, "https://example.com/ir/calendar/")

        result = discover_ir_page("1234", use_llm_fallback=False)

        assert result is not None
        assert result.url == "https://example.com/ir/calendar/"
        assert result.company_code == "1234"
        assert result.company_name == "Example Corp"
        assert result.discovered_via == "pattern"

    @patch("pykabu_calendar.earnings.ir.discovery.Ticker")
    def test_no_website(self, mock_ticker):
        """Test handling company with no website."""
        mock_profile = Mock()
        mock_profile.website = None
        mock_profile.name = "No Website Corp"
        mock_ticker.return_value.profile = mock_profile

        result = discover_ir_page("1234", use_llm_fallback=False)
        assert result is None

    @patch("pykabu_calendar.earnings.ir.discovery.Ticker")
    def test_ticker_error(self, mock_ticker):
        """Test handling pykabutan error."""
        mock_ticker.side_effect = ValueError("API error")

        result = discover_ir_page("9999", use_llm_fallback=False)
        assert result is None

    @patch("pykabu_calendar.earnings.ir.discovery.Ticker")
    @patch("pykabu_calendar.earnings.ir.discovery._check_url_exists")
    @patch("pykabu_calendar.earnings.ir.discovery.fetch_safe")
    def test_discovers_via_homepage_link(self, mock_fetch, mock_check, mock_ticker):
        """Test discovering IR page via homepage link."""
        # Setup mock ticker
        mock_profile = Mock()
        mock_profile.website = "https://example.com/"
        mock_profile.name = "Example Corp"
        mock_ticker.return_value.profile = mock_profile

        # Pattern matching fails for all candidates, then homepage link succeeds
        # Use a unique path that won't be in standard patterns
        def check_url_side_effect(url, timeout=10):
            if "/special-ir-page/" in url:
                return (True, "https://example.com/special-ir-page/")
            return (False, None)

        mock_check.side_effect = check_url_side_effect
        mock_fetch.return_value = '<a href="/special-ir-page/">IR情報</a>'

        result = discover_ir_page("1234", use_llm_fallback=False)

        assert result is not None
        assert "special-ir-page" in result.url
        assert result.discovered_via == "homepage_link"


@pytest.mark.slow
class TestDiscoverIrPageIntegration:
    """Integration tests for discover_ir_page (requires network)."""

    def test_toyota(self):
        """Test discovering Toyota's IR page."""
        result = discover_ir_page("7203", use_llm_fallback=False, timeout=15)
        assert result is not None
        assert result.company_code == "7203"
        assert "ir" in result.url.lower() or "investor" in result.url.lower()

    def test_softbank(self):
        """Test discovering SoftBank Group's IR page."""
        result = discover_ir_page("9984", use_llm_fallback=False, timeout=15)
        assert result is not None
        assert result.company_code == "9984"

    def test_unknown_code(self):
        """Test with unknown stock code."""
        result = discover_ir_page("0000", use_llm_fallback=False, timeout=5)
        assert result is None
