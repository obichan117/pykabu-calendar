"""Tests for core/fetch.py — session management and fetch functions."""

from unittest.mock import patch, MagicMock

import pytest
import requests

from pykabu_calendar.core.fetch import get_session, fetch, fetch_safe, _reset_sessions


class TestGetSession:
    """Tests for thread-local session management."""

    def test_returns_session(self):
        _reset_sessions()
        session = get_session()
        assert isinstance(session, requests.Session)

    def test_returns_same_session_per_thread(self):
        _reset_sessions()
        s1 = get_session()
        s2 = get_session()
        assert s1 is s2

    def test_session_has_default_headers(self):
        _reset_sessions()
        session = get_session()
        assert "User-Agent" in session.headers

    def test_reset_bumps_version_creates_new_session(self):
        _reset_sessions()
        s1 = get_session()
        _reset_sessions()
        s2 = get_session()
        assert s1 is not s2

    def test_other_thread_detects_version_change(self):
        import threading

        _reset_sessions()
        s1 = get_session()
        _reset_sessions()  # bump version

        other_session = [None]

        def worker():
            other_session[0] = get_session()

        t = threading.Thread(target=worker)
        t.start()
        t.join()

        # Other thread should get a fresh session, not s1
        assert other_session[0] is not s1


class TestFetch:
    """Tests for fetch() — raises on failure."""

    @patch("pykabu_calendar.core.fetch.get_session")
    def test_returns_text(self, mock_get_session):
        mock_response = MagicMock()
        mock_response.text = "<html>OK</html>"
        mock_response.apparent_encoding = "utf-8"
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_get_session.return_value = mock_session

        result = fetch("https://example.com")
        assert result == "<html>OK</html>"

    @patch("pykabu_calendar.core.fetch.get_session")
    def test_raises_on_http_error(self, mock_get_session):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404")
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_get_session.return_value = mock_session

        with pytest.raises(requests.HTTPError):
            fetch("https://example.com/missing")

    @patch("pykabu_calendar.core.fetch.get_session")
    def test_uses_settings_timeout(self, mock_get_session):
        mock_response = MagicMock()
        mock_response.text = ""
        mock_response.apparent_encoding = "utf-8"
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_get_session.return_value = mock_session

        fetch("https://example.com")
        _, kwargs = mock_session.get.call_args
        assert "timeout" in kwargs

    @patch("pykabu_calendar.core.fetch.get_session")
    def test_custom_timeout(self, mock_get_session):
        mock_response = MagicMock()
        mock_response.text = ""
        mock_response.apparent_encoding = "utf-8"
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_get_session.return_value = mock_session

        fetch("https://example.com", timeout=5)
        _, kwargs = mock_session.get.call_args
        assert kwargs["timeout"] == 5


class TestFetchSafe:
    """Tests for fetch_safe() — returns None on failure."""

    @patch("pykabu_calendar.core.fetch.get_session")
    def test_returns_text_on_success(self, mock_get_session):
        mock_response = MagicMock()
        mock_response.text = "OK"
        mock_response.apparent_encoding = "utf-8"
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_get_session.return_value = mock_session

        assert fetch_safe("https://example.com") == "OK"

    @patch("pykabu_calendar.core.fetch.get_session")
    def test_returns_none_on_failure(self, mock_get_session):
        mock_session = MagicMock()
        mock_session.get.side_effect = requests.ConnectionError("timeout")
        mock_get_session.return_value = mock_session

        assert fetch_safe("https://example.com") is None

    @patch("pykabu_calendar.core.fetch.get_session")
    def test_returns_none_on_http_error(self, mock_get_session):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("500")
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_get_session.return_value = mock_session

        assert fetch_safe("https://example.com") is None
