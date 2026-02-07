"""Gemini LLM provider for IR discovery."""

import logging
import os
import time
from threading import Lock

from google import genai
from google.genai import types

from .base import LLMClient, LLMResponse

logger = logging.getLogger(__name__)

# Default model - free tier friendly
DEFAULT_MODEL = "gemini-2.0-flash"

# Rate limiting for free tier: 15 RPM
RATE_LIMIT_RPM = 15
MIN_REQUEST_INTERVAL = 60.0 / RATE_LIMIT_RPM  # ~4 seconds


class GeminiClient(LLMClient):
    """Google Gemini API client using free tier.

    Free tier limits:
    - 15 requests per minute
    - 1 million tokens per day
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        timeout: float = 60.0,
    ) -> None:
        """Initialize Gemini client.

        Args:
            api_key: Gemini API key. If None, uses GEMINI_API_KEY env var.
            model: Model to use (default: gemini-2.0-flash).
            timeout: Request timeout in seconds.
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model = model
        self.timeout = timeout
        self._client: genai.Client | None = None

        # Rate limiting
        self._last_request_time: float = 0.0
        self._rate_lock = Lock()

    def _get_client(self) -> genai.Client:
        """Get or create the Gemini client."""
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
        """Wait if needed to respect rate limits."""
        with self._rate_lock:
            now = time.time()
            elapsed = now - self._last_request_time
            if elapsed < MIN_REQUEST_INTERVAL:
                wait_time = MIN_REQUEST_INTERVAL - elapsed
                logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
                time.sleep(wait_time)
            self._last_request_time = time.time()

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
            config = types.GenerateContentConfig(
                temperature=0.1,  # Low temp for factual extraction
                max_output_tokens=1024,
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

        except Exception as e:
            error_msg = str(e).lower()

            if "quota" in error_msg or "rate" in error_msg or "exhausted" in error_msg:
                logger.warning(f"Rate limit exceeded: {e}")
                raise RuntimeError(
                    "Gemini rate limit exceeded. Please wait and try again."
                ) from e

            if "permission" in error_msg or "api key" in error_msg or "401" in error_msg:
                logger.error(f"Authentication failed: {e}")
                raise ValueError(
                    "Invalid Gemini API key. Check GEMINI_API_KEY environment variable."
                ) from e

            if "invalid" in error_msg or "400" in error_msg:
                logger.error(f"Invalid request: {e}")
                raise RuntimeError(f"Invalid request to Gemini API: {e}") from e

            logger.error(f"Gemini API error: {e}")
            raise RuntimeError(f"Gemini API error: {e}") from e
