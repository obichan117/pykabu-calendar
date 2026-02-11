"""Gemini LLM provider for IR discovery."""

import logging
import os
import time
from threading import Lock

try:
    from google import genai
    from google.genai import types
    from google.genai.errors import APIError, ClientError, ServerError
except ImportError:
    genai = None  # type: ignore[assignment]
    types = None  # type: ignore[assignment]
    APIError = None  # type: ignore[assignment,misc]
    ClientError = None  # type: ignore[assignment,misc]
    ServerError = None  # type: ignore[assignment,misc]

from ..config import get_settings
from .base import LLMClient, LLMResponse

logger = logging.getLogger(__name__)



class GeminiClient(LLMClient):
    """Google Gemini API client using free tier.

    Free tier limits:
    - 15 requests per minute
    - 1 million tokens per day
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
    ) -> None:
        """Initialize Gemini client.

        Args:
            api_key: Gemini API key. If None, uses GEMINI_API_KEY env var.
            model: Model to use. If None, uses ``get_settings().llm_model``.
            timeout: Request timeout in seconds. If None, uses ``get_settings().llm_timeout``.
        """
        if genai is None:
            raise ImportError(
                "google-genai is required for GeminiClient. "
                "Install it with: pip install pykabu-calendar[llm]"
            )

        settings = get_settings()
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model = model if model is not None else settings.llm_model
        self.timeout = timeout if timeout is not None else settings.llm_timeout
        self._client: genai.Client | None = None
        self._client_lock = Lock()

        # Rate limiting (from settings)
        self._last_request_time: float = 0.0
        self._next_request_time: float = 0.0
        self._rate_lock = Lock()
        rpm = settings.llm_rate_limit_rpm
        self._min_request_interval = 60.0 / rpm if rpm > 0 else 0.0

    def _get_client(self) -> "genai.Client":
        """Get or create the Gemini client (thread-safe)."""
        if self._client is not None:
            return self._client

        with self._client_lock:
            if self._client is not None:
                return self._client

            if not self.api_key:
                raise ValueError(
                    "Gemini API key required. Set GEMINI_API_KEY environment variable "
                    "or pass api_key to GeminiClient."
                )

            self._client = genai.Client(api_key=self.api_key)
            return self._client

    def _wait_for_rate_limit(self) -> None:
        """Wait if needed to respect rate limits (does not hold lock while sleeping)."""
        with self._rate_lock:
            now = time.time()
            wait_time = max(0.0, self._next_request_time - now)
            self._next_request_time = now + wait_time + self._min_request_interval

        if wait_time > 0:
            logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
            time.sleep(wait_time)

    def complete(self, prompt: str, system: str | None = None) -> LLMResponse:
        """Send a prompt to Gemini and get a response.

        Args:
            prompt: The user prompt.
            system: Optional system prompt.

        Returns:
            LLMResponse with content and metadata.

        Raises:
            ValueError: If API key is not configured.
            RuntimeError: If API call fails.
        """
        self._wait_for_rate_limit()

        client = self._get_client()

        try:
            # Build generation config
            settings = get_settings()
            config = types.GenerateContentConfig(
                temperature=settings.llm_temperature,
                max_output_tokens=settings.llm_max_output_tokens,
                system_instruction=system,
            )

            response = client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config,
            )

            # Extract token counts
            input_tokens = None
            output_tokens = None
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                input_tokens = response.usage_metadata.prompt_token_count
                output_tokens = response.usage_metadata.candidates_token_count

            return LLMResponse(
                content=response.text or "",
                model=self.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )

        except ClientError as e:
            if e.code == 429 or (e.status and "RESOURCE_EXHAUSTED" in e.status):
                logger.warning(f"Rate limit exceeded: {e}")
                raise RuntimeError(
                    "Gemini rate limit exceeded. Please wait and try again."
                ) from e
            if e.code in (401, 403):
                logger.error(f"Authentication failed: {e}")
                raise ValueError(
                    "Invalid Gemini API key. Check GEMINI_API_KEY environment variable."
                ) from e
            logger.error(f"Gemini client error: {e}")
            raise RuntimeError(f"Gemini API client error: {e}") from e
        except ServerError as e:
            logger.error(f"Gemini server error: {e}")
            raise RuntimeError(f"Gemini API server error: {e}") from e
        except APIError as e:
            logger.error(f"Gemini API error: {e}")
            raise RuntimeError(f"Gemini API error: {e}") from e
