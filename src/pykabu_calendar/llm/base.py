"""Base LLM client interface for IR discovery."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from ..config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Response from LLM call."""

    content: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None


class LLMClient(ABC):
    """Abstract base class for LLM providers.

    Used for IR page discovery and parsing when rule-based methods fail.
    """

    @abstractmethod
    def complete(self, prompt: str, system: str | None = None) -> LLMResponse:
        """Send a prompt to the LLM and get a response.

        Args:
            prompt: The user prompt
            system: Optional system prompt

        Returns:
            LLMResponse with content and metadata
        """
        pass

    def find_link(self, html: str, description: str) -> str | None:
        """Find a link in HTML matching the description.

        Args:
            html: HTML content to search
            description: What to look for (e.g., "IR page", "earnings calendar")

        Returns:
            URL string if found, None otherwise
        """
        # Truncate HTML to avoid token limits
        max_chars = get_settings().llm_find_link_max_chars
        if len(html) > max_chars:
            html = html[:max_chars] + "\n... (truncated)"

        system = """You are an expert at finding links in HTML.
Extract the URL that best matches the user's description.
Return ONLY the URL, nothing else. If not found, return "NOT_FOUND"."""

        prompt = f"""Find the {description} link in this HTML:

{html}

Return only the URL (starting with http or /), or "NOT_FOUND" if not present."""

        try:
            response = self.complete(prompt, system)
            result = response.content.strip()

            if result == "NOT_FOUND" or not result:
                return None

            # Clean up the URL
            if result.startswith('"') or result.startswith("'"):
                result = result[1:-1]

            return result if result.startswith(("http", "/")) else None

        except Exception as e:
            logger.warning(f"LLM find_link failed: {e}")
            return None

    def extract_datetime(
        self, html: str, context: str | None = None
    ) -> datetime | None:
        """Extract earnings announcement datetime from HTML.

        Args:
            html: HTML content containing earnings info
            context: Optional context (company name, expected date range)

        Returns:
            Parsed datetime if found, None otherwise
        """
        # Truncate HTML to avoid token limits
        max_chars = get_settings().llm_extract_datetime_max_chars
        if len(html) > max_chars:
            html = html[:max_chars] + "\n... (truncated)"

        system = """You are an expert at extracting earnings announcement dates and times from Japanese company IR pages.
Look for patterns like:
- 決算発表日
- 決算発表予定
- 業績発表
- YYYY年MM月DD日 HH:MM
- YYYY/MM/DD HH時MM分

Return the datetime in ISO format: YYYY-MM-DDTHH:MM:SS
If only date is found (no time), use T00:00:00
If not found, return "NOT_FOUND"."""

        context_str = f"\nContext: {context}" if context else ""
        prompt = f"""Extract the earnings announcement datetime from this HTML:{context_str}

{html}

Return only the datetime in ISO format (YYYY-MM-DDTHH:MM:SS), or "NOT_FOUND"."""

        try:
            response = self.complete(prompt, system)
            result = response.content.strip()

            if result == "NOT_FOUND" or not result:
                return None

            # Clean up and parse
            result = result.replace('"', "").replace("'", "")
            return datetime.fromisoformat(result)

        except ValueError as e:
            logger.warning(f"Failed to parse datetime: {e}")
            return None
        except Exception as e:
            logger.warning(f"LLM extract_datetime failed: {e}")
            return None
