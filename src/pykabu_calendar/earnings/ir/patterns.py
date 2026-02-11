"""Common IR page URL patterns for Japanese companies."""

import logging
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

# Common paths for main IR landing pages
IR_PATH_PATTERNS = [
    "/ir/",
    "/investor/",
    "/investors/",
    "/ir.html",
    "/corporate/ir/",
    "/about/ir/",
    "/company/ir/",
    "/jp/ir/",
    "/ja/ir/",
    "/ja-jp/ir/",
    # Japanese equivalents
    "/ir/index.html",
    "/ir/index.htm",
]

# Common paths for earnings calendar/schedule pages
CALENDAR_PATH_PATTERNS = [
    # Direct calendar pages
    "/ir/calendar/",
    "/ir/calendar.html",
    "/ir/schedule/",
    "/ir/schedule.html",
    "/ir/event/",
    "/ir/events/",
    # Japanese terms
    "/ir/kessan/",  # 決算
    "/ir/gyoseki/",  # 業績
    "/ir/zaimu/",  # 財務
    # Library/news pages (often contain earnings info)
    "/ir/library/",
    "/ir/news/",
    "/ir/release/",
    "/ir/whatsnew/",
    # Stock/shareholder pages
    "/ir/stock/",
    "/ir/kabunushi/",  # 株主
    # Other common patterns
    "/ir/financial/",
    "/ir/finance/",
    "/ir/results/",
    "/ir/data/",
]

# Known IR platform domains (some companies host IR on external platforms)
KNOWN_IR_PLATFORMS = [
    "irbank.net",
    "ir-site.jp",
    "pronexus.co.jp",
    "eir-parts.net",
]


def normalize_base_url(url: str) -> str:
    """Normalize a company website URL to a base URL for pattern matching.

    Args:
        url: Company website URL (e.g., https://www.example.co.jp/about/)

    Returns:
        Normalized base URL (e.g., https://www.example.co.jp)
    """
    if not url:
        return ""

    # Ensure scheme
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)

    # Return just scheme + netloc (no path)
    return f"{parsed.scheme}://{parsed.netloc}"


def get_candidate_urls(
    base_url: str,
    include_calendar: bool = True,
    include_ir_landing: bool = True,
) -> list[str]:
    """Generate candidate IR page URLs from a company's base website URL.

    Args:
        base_url: Company website URL (e.g., https://www.toyota.co.jp/)
        include_calendar: Include calendar/schedule specific paths
        include_ir_landing: Include main IR landing page paths

    Returns:
        List of candidate URLs to check, ordered by likelihood
    """
    if not base_url:
        return []

    # Normalize the base URL
    normalized = normalize_base_url(base_url)
    if not normalized:
        return []

    candidates = []
    seen = set()

    def add_candidate(path: str) -> None:
        """Add a candidate URL, avoiding duplicates."""
        full_url = urljoin(normalized, path)
        if full_url not in seen:
            seen.add(full_url)
            candidates.append(full_url)

    # Priority 1: Calendar/schedule pages (most specific)
    if include_calendar:
        for pattern in CALENDAR_PATH_PATTERNS:
            add_candidate(pattern)

    # Priority 2: Main IR landing pages
    if include_ir_landing:
        for pattern in IR_PATH_PATTERNS:
            add_candidate(pattern)

    # Priority 3: Try original URL path + /ir/ if it has a path
    parsed = urlparse(base_url)
    if parsed.path and parsed.path != "/":
        # e.g., https://example.com/company/jp/ -> https://example.com/company/jp/ir/
        path_with_ir = parsed.path.rstrip("/") + "/ir/"
        add_candidate(path_with_ir)

    logger.debug(f"Generated {len(candidates)} candidate URLs for {base_url}")
    return candidates


def extract_ir_keywords() -> list[str]:
    """Get list of keywords that typically indicate IR content.

    Returns:
        List of Japanese and English IR-related keywords
    """
    return [
        # English
        "investor relations",
        "ir information",
        "financial results",
        "earnings",
        "quarterly results",
        # Japanese
        "IR情報",
        "投資家情報",
        "株主・投資家",
        "決算情報",
        "決算発表",
        "業績",
        "財務情報",
        "決算短信",
        "決算説明会",
        "決算カレンダー",
        "IRカレンダー",
    ]
