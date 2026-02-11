"""Parse earnings datetime from company IR pages."""

import logging
import re
from dataclasses import dataclass
from datetime import datetime, time
from enum import Enum

import requests
from bs4 import BeautifulSoup

from ...config import TIMEOUT
from ...core.fetch import fetch
from ...llm import LLMClient, get_default_client

logger = logging.getLogger(__name__)


class ParseConfidence(Enum):
    """Confidence level of parsed result."""

    HIGH = "high"  # Clear, unambiguous match
    MEDIUM = "medium"  # Reasonable match, some uncertainty
    LOW = "low"  # Weak match, may need verification


@dataclass
class EarningsInfo:
    """Parsed earnings announcement information."""

    datetime: datetime | None
    confidence: ParseConfidence
    source: str  # "rule" or "llm"
    raw_text: str | None = None  # Original text that was parsed
    has_time: bool = True  # Whether time was explicitly found

    def __str__(self) -> str:
        dt_str = self.datetime.isoformat() if self.datetime else "None"
        return f"EarningsInfo({dt_str}, {self.confidence.value}, via {self.source})"


# Japanese date patterns
DATE_PATTERNS = [
    # 2025年2月14日 or 2025年02月14日
    (r"(\d{4})年(\d{1,2})月(\d{1,2})日", "%Y-%m-%d"),
    # 2025/2/14 or 2025/02/14
    (r"(\d{4})/(\d{1,2})/(\d{1,2})", "%Y-%m-%d"),
    # 2025-02-14
    (r"(\d{4})-(\d{1,2})-(\d{1,2})", "%Y-%m-%d"),
    # 令和7年2月14日 (Japanese era - Reiwa started 2019)
    (r"令和(\d{1,2})年(\d{1,2})月(\d{1,2})日", "reiwa"),
]

# Japanese time patterns (order matters - more specific patterns first)
TIME_PATTERNS = [
    # 15:00
    (r"(\d{1,2}):(\d{2})", "24h"),
    # 午後3時30分 (PM with minutes - must come before hour-only)
    (r"午後(\d{1,2})時(\d{1,2})分", "pm"),
    # 午後3時 (PM hour only)
    (r"午後(\d{1,2})時", "pm_hour_only"),
    # 午前11時30分 (AM with minutes)
    (r"午前(\d{1,2})時(\d{1,2})分", "am"),
    # 午前11時 (AM hour only)
    (r"午前(\d{1,2})時", "am_hour_only"),
    # 15時00分 (24h with minutes - after AM/PM to avoid matching 午後3時)
    (r"(\d{1,2})時(\d{1,2})分", "24h"),
    # 15時 (24h hour only - last, most generic)
    (r"(\d{1,2})時", "24h_hour_only"),
]

# Keywords indicating earnings announcement
EARNINGS_KEYWORDS = [
    "決算発表",
    "決算発表予定",
    "決算短信",
    "四半期決算",
    "本決算",
    "業績発表",
    "決算日",
    "決算説明会",
    "earnings",
    "financial results",
]

# Keywords indicating time is undetermined (lowercase for comparison)
UNDETERMINED_KEYWORDS = [
    "未定",
    "未確定",
    "調整中",
    "tbd",
    "undetermined",
]


def _parse_japanese_date(text: str) -> tuple[datetime | None, str | None]:
    """Parse Japanese date from text.

    Args:
        text: Text containing date

    Returns:
        Tuple of (datetime date only, matched text)
    """
    for pattern, fmt in DATE_PATTERNS:
        match = re.search(pattern, text)
        if match:
            try:
                if fmt == "reiwa":
                    # Convert Reiwa year to Gregorian
                    year = 2018 + int(match.group(1))
                    month = int(match.group(2))
                    day = int(match.group(3))
                else:
                    year = int(match.group(1))
                    month = int(match.group(2))
                    day = int(match.group(3))

                dt = datetime(year, month, day)
                return dt, match.group(0)
            except ValueError:
                continue
    return None, None


def _parse_japanese_time(text: str) -> tuple[time | None, str | None]:
    """Parse Japanese time from text.

    Args:
        text: Text containing time

    Returns:
        Tuple of (time object, matched text)
    """
    for pattern, fmt in TIME_PATTERNS:
        match = re.search(pattern, text)
        if match:
            try:
                if fmt == "24h":
                    hour = int(match.group(1))
                    minute = int(match.group(2))
                elif fmt == "24h_hour_only":
                    hour = int(match.group(1))
                    minute = 0
                elif fmt in ("pm", "pm_hour_only"):
                    hour = int(match.group(1))
                    if hour != 12:
                        hour += 12
                    minute = int(match.group(2)) if fmt == "pm" else 0
                elif fmt in ("am", "am_hour_only"):
                    hour = int(match.group(1))
                    if hour == 12:
                        hour = 0
                    minute = int(match.group(2)) if fmt == "am" else 0
                else:
                    continue

                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    return time(hour, minute), match.group(0)
            except ValueError:
                continue
    return None, None


def _has_undetermined_marker(text: str) -> bool:
    """Check if text indicates time is undetermined."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in UNDETERMINED_KEYWORDS)


def _fetch_html(url: str, timeout: int = TIMEOUT) -> str | None:
    """Fetch HTML from URL."""
    try:
        return fetch(url, timeout=timeout)
    except requests.RequestException as e:
        logger.debug(f"Failed to fetch {url}: {e}")
        return None


def _find_earnings_context(soup: BeautifulSoup, code: str | None = None) -> list[str]:
    """Find text blocks that likely contain earnings info.

    Args:
        soup: BeautifulSoup object
        code: Optional stock code to look for

    Returns:
        List of text blocks that may contain earnings datetime
    """
    contexts = []

    # Look for tables with earnings keywords
    for table in soup.find_all("table"):
        table_text = table.get_text(" ", strip=True)
        if any(kw in table_text for kw in EARNINGS_KEYWORDS):
            # Get each row as context
            for row in table.find_all("tr"):
                row_text = row.get_text(" ", strip=True)
                if row_text:
                    contexts.append(row_text)

    # Look for divs/sections with earnings keywords
    for elem in soup.find_all(["div", "section", "article", "p", "li"]):
        text = elem.get_text(" ", strip=True)
        if len(text) < 500 and any(kw in text for kw in EARNINGS_KEYWORDS):
            contexts.append(text)

    # If code provided, look for rows containing the code
    if code:
        for elem in soup.find_all(string=re.compile(code)):
            parent = elem.find_parent(["tr", "div", "p", "li"])
            if parent:
                contexts.append(parent.get_text(" ", strip=True))

    # Deduplicate while preserving order
    seen = set()
    unique_contexts = []
    for ctx in contexts:
        if ctx not in seen and len(ctx) > 10:
            seen.add(ctx)
            unique_contexts.append(ctx)

    return unique_contexts[:20]  # Limit to top 20


def _parse_context_rule_based(context: str) -> EarningsInfo | None:
    """Try to parse earnings datetime from a context string.

    Args:
        context: Text that may contain earnings datetime

    Returns:
        EarningsInfo if successfully parsed, None otherwise
    """
    # Check for undetermined marker
    if _has_undetermined_marker(context):
        date_dt, date_text = _parse_japanese_date(context)
        if date_dt:
            return EarningsInfo(
                datetime=date_dt,
                confidence=ParseConfidence.MEDIUM,
                source="rule",
                raw_text=context[:200],
                has_time=False,
            )

    # Try to find date
    date_dt, date_text = _parse_japanese_date(context)
    if not date_dt:
        return None

    # Try to find time near the date
    time_obj, time_text = _parse_japanese_time(context)

    if time_obj:
        # Combine date and time
        full_dt = datetime.combine(date_dt.date(), time_obj)
        return EarningsInfo(
            datetime=full_dt,
            confidence=ParseConfidence.HIGH,
            source="rule",
            raw_text=context[:200],
            has_time=True,
        )
    else:
        # Date only
        return EarningsInfo(
            datetime=date_dt,
            confidence=ParseConfidence.MEDIUM,
            source="rule",
            raw_text=context[:200],
            has_time=False,
        )


def parse_earnings_datetime(
    url: str,
    code: str | None = None,
    llm_client: LLMClient | None = None,
    use_llm_fallback: bool = True,
    timeout: int = TIMEOUT,
) -> EarningsInfo | None:
    """Parse earnings announcement datetime from an IR page.

    Args:
        url: URL of the IR page
        code: Optional stock code to help locate relevant info
        llm_client: Optional LLM client for fallback parsing
        use_llm_fallback: Whether to use LLM as fallback
        timeout: Request timeout in seconds

    Returns:
        EarningsInfo if found, None otherwise
    """
    logger.info(f"Parsing earnings datetime from {url}")

    # Fetch the page
    html = _fetch_html(url, timeout=timeout)
    if not html:
        return None

    soup = BeautifulSoup(html, "lxml")

    # Find contexts that likely contain earnings info
    contexts = _find_earnings_context(soup, code)
    logger.debug(f"Found {len(contexts)} potential contexts")

    # Try rule-based parsing on each context
    best_result: EarningsInfo | None = None

    for context in contexts:
        result = _parse_context_rule_based(context)
        if result:
            # Prefer results with time over date-only
            if result.has_time:
                logger.info(f"Found earnings datetime via rule: {result}")
                return result
            elif best_result is None or not best_result.has_time:
                best_result = result

    if best_result:
        logger.info(f"Found earnings date via rule: {best_result}")
        return best_result

    # LLM fallback
    if use_llm_fallback:
        if llm_client is None:
            llm_client = get_default_client()

        if llm_client is None:
            return None

        logger.debug("Using LLM to extract earnings datetime")

        # Build context for LLM
        context_hint = f" for stock code {code}" if code else ""
        llm_html = "\n".join(contexts[:10]) if contexts else soup.get_text()[:10000]

        result_dt = llm_client.extract_datetime(llm_html, context=context_hint)
        if result_dt:
            return EarningsInfo(
                datetime=result_dt,
                confidence=ParseConfidence.MEDIUM,
                source="llm",
                raw_text=None,
                has_time=result_dt.hour != 0 or result_dt.minute != 0,
            )

    logger.info(f"Could not find earnings datetime in {url}")
    return None


def parse_earnings_from_html(
    html: str,
    code: str | None = None,
    llm_client: LLMClient | None = None,
    use_llm_fallback: bool = True,
) -> EarningsInfo | None:
    """Parse earnings datetime from HTML content directly.

    Args:
        html: HTML content
        code: Optional stock code
        llm_client: Optional LLM client
        use_llm_fallback: Whether to use LLM fallback

    Returns:
        EarningsInfo if found, None otherwise
    """
    soup = BeautifulSoup(html, "lxml")
    contexts = _find_earnings_context(soup, code)

    best_result: EarningsInfo | None = None

    for context in contexts:
        result = _parse_context_rule_based(context)
        if result:
            if result.has_time:
                return result
            elif best_result is None or not best_result.has_time:
                best_result = result

    if best_result:
        return best_result

    # LLM fallback
    if use_llm_fallback and llm_client:
        result_dt = llm_client.extract_datetime(html, context=code)
        if result_dt:
            return EarningsInfo(
                datetime=result_dt,
                confidence=ParseConfidence.MEDIUM,
                source="llm",
                raw_text=None,
                has_time=result_dt.hour != 0 or result_dt.minute != 0,
            )

    return None
