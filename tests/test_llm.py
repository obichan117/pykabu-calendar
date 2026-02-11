"""Tests for LLM module."""

import os
import pytest
from datetime import datetime
from unittest.mock import patch

from pykabu_calendar.llm import LLMClient, LLMResponse, GeminiClient


class TestLLMResponse:
    """Tests for LLMResponse dataclass."""

    def test_basic_response(self):
        """Test creating a basic response."""
        response = LLMResponse(
            content="Hello",
            model="test-model",
        )
        assert response.content == "Hello"
        assert response.model == "test-model"
        assert response.input_tokens is None
        assert response.output_tokens is None

    def test_response_with_tokens(self):
        """Test response with token counts."""
        response = LLMResponse(
            content="Hello",
            model="test-model",
            input_tokens=10,
            output_tokens=5,
        )
        assert response.input_tokens == 10
        assert response.output_tokens == 5


class TestLLMClientInterface:
    """Tests for LLMClient abstract interface."""

    def test_cannot_instantiate_abstract(self):
        """Test that LLMClient cannot be instantiated directly."""
        with pytest.raises(TypeError):
            LLMClient()

    def test_concrete_implementation(self):
        """Test that concrete implementation works."""

        class MockClient(LLMClient):
            def complete(self, prompt, system=None):
                return LLMResponse(content="mock", model="mock")

        client = MockClient()
        response = client.complete("test")
        assert response.content == "mock"


class TestGeminiClient:
    """Tests for GeminiClient."""

    def test_init_with_api_key(self):
        """Test initialization with explicit API key."""
        client = GeminiClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.model == "gemini-2.0-flash"
        assert client.timeout == 60.0

    def test_init_with_env_var(self):
        """Test initialization with environment variable."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "env-key"}):
            client = GeminiClient()
            assert client.api_key == "env-key"

    def test_init_custom_model(self):
        """Test initialization with custom model."""
        client = GeminiClient(api_key="test", model="gemini-1.5-pro")
        assert client.model == "gemini-1.5-pro"

    def test_get_client_requires_api_key(self):
        """Test that get_client raises without API key."""
        client = GeminiClient(api_key=None)
        # Clear any env var
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}, clear=False):
            client.api_key = None
            with pytest.raises(ValueError, match="API key required"):
                client._get_client()


class TestFindLink:
    """Tests for find_link method."""

    def test_find_link_with_mock(self):
        """Test find_link using mock."""

        class MockClient(LLMClient):
            def complete(self, prompt, system=None):
                return LLMResponse(
                    content="https://example.com/ir",
                    model="mock",
                )

        client = MockClient()
        result = client.find_link("<html>test</html>", "IR page")
        assert result == "https://example.com/ir"

    def test_find_link_not_found(self):
        """Test find_link when not found."""

        class MockClient(LLMClient):
            def complete(self, prompt, system=None):
                return LLMResponse(content="NOT_FOUND", model="mock")

        client = MockClient()
        result = client.find_link("<html>test</html>", "IR page")
        assert result is None

    def test_find_link_cleans_quotes(self):
        """Test that find_link removes quotes."""

        class MockClient(LLMClient):
            def complete(self, prompt, system=None):
                return LLMResponse(
                    content='"https://example.com/ir"',
                    model="mock",
                )

        client = MockClient()
        result = client.find_link("<html></html>", "IR page")
        assert result == "https://example.com/ir"

    def test_find_link_relative_url(self):
        """Test find_link with relative URL."""

        class MockClient(LLMClient):
            def complete(self, prompt, system=None):
                return LLMResponse(content="/ir/index.html", model="mock")

        client = MockClient()
        result = client.find_link("<html></html>", "IR page")
        assert result == "/ir/index.html"

    def test_find_link_invalid_url(self):
        """Test find_link with invalid URL."""

        class MockClient(LLMClient):
            def complete(self, prompt, system=None):
                return LLMResponse(content="not a url", model="mock")

        client = MockClient()
        result = client.find_link("<html></html>", "IR page")
        assert result is None


class TestExtractDatetime:
    """Tests for extract_datetime method."""

    def test_extract_datetime_with_mock(self):
        """Test extract_datetime using mock."""

        class MockClient(LLMClient):
            def complete(self, prompt, system=None):
                return LLMResponse(
                    content="2025-02-14T15:00:00",
                    model="mock",
                )

        client = MockClient()
        result = client.extract_datetime("<html>決算発表</html>")
        assert result == datetime(2025, 2, 14, 15, 0, 0)

    def test_extract_datetime_not_found(self):
        """Test extract_datetime when not found."""

        class MockClient(LLMClient):
            def complete(self, prompt, system=None):
                return LLMResponse(content="NOT_FOUND", model="mock")

        client = MockClient()
        result = client.extract_datetime("<html></html>")
        assert result is None

    def test_extract_datetime_invalid_format(self):
        """Test extract_datetime with invalid format."""

        class MockClient(LLMClient):
            def complete(self, prompt, system=None):
                return LLMResponse(content="invalid", model="mock")

        client = MockClient()
        result = client.extract_datetime("<html></html>")
        assert result is None

    def test_extract_datetime_with_context(self):
        """Test extract_datetime with context."""

        class MockClient(LLMClient):
            def complete(self, prompt, system=None):
                # Verify context is in prompt
                assert "Toyota" in prompt
                return LLMResponse(
                    content="2025-02-14T00:00:00",
                    model="mock",
                )

        client = MockClient()
        result = client.extract_datetime("<html></html>", context="Toyota")
        assert result is not None


@pytest.mark.skipif(
    not os.environ.get("GEMINI_API_KEY"),
    reason="GEMINI_API_KEY not set",
)
class TestGeminiIntegration:
    """Integration tests requiring actual API key."""

    def test_complete_simple(self):
        """Test simple completion."""
        client = GeminiClient()
        response = client.complete("What is 2+2? Reply with just the number.")
        assert "4" in response.content
        assert response.model == "gemini-2.0-flash"

    def test_complete_with_system(self):
        """Test completion with system prompt."""
        client = GeminiClient()
        response = client.complete(
            "What is the capital of Japan?",
            system="You are a helpful assistant. Reply concisely.",
        )
        assert "Tokyo" in response.content or "東京" in response.content

    def test_find_link_real(self):
        """Test find_link with real HTML."""
        html = """
        <html>
        <body>
            <a href="/corporate/ir/">Investor Relations</a>
            <a href="/about/">About Us</a>
            <a href="/products/">Products</a>
        </body>
        </html>
        """
        client = GeminiClient()
        result = client.find_link(html, "IR page or Investor Relations page")
        assert result is not None
        assert "ir" in result.lower()
