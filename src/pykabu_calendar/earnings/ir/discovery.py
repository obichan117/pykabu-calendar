"""IR page discovery - find company investor relations pages."""

import logging
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pykabutan import Ticker

from ...config import get_settings
from ...core.fetch import fetch_safe, get_session
from ...core.parse import HTML_PARSER
from ...llm import LLMClient, get_default_client
from .patterns import get_candidate_urls, extract_ir_keywords

logger = logging.getLogger(__name__)


class IRPageType(Enum):
    """Type of IR page discovered."""

    CALENDAR = "calendar"  # Dedicated earnings calendar page
    NEWS = "news"  # IR news/releases page
    LIBRARY = "library"  # IR library/documents page
    LANDING = "landing"  # Main IR landing page
    UNKNOWN = "unknown"  # Could not determine type


@dataclass
class IRPageInfo:
    """Information about a discovered IR page."""

    url: str
    page_type: IRPageType
    company_code: str
    company_name: str | None = None
    discovered_via: str = "pattern"  # "pattern", "llm", "homepage_link"

    def __str__(self) -> str:
        return f"IRPageInfo({self.company_code}: {self.url} [{self.page_type.value}])"


def _check_url_exists(url: str, timeout: int | None = None) -> tuple[bool, str | None]:
    """Check if a URL exists and is accessible.

    Args:
        url: URL to check
        timeout: Request timeout in seconds

    Returns:
        Tuple of (exists, final_url after redirects)
    """
    if timeout is None:
        timeout = get_settings().timeout
    session = get_session()
    try:
        response = session.head(url, timeout=timeout, allow_redirects=True)
        if response.status_code == 200:
            return True, response.url

        # Some servers don't support HEAD, try GET
        if response.status_code in (403, 405):
            response = session.get(
                url, timeout=timeout, allow_redirects=True, stream=True,
            )
            response.close()
            if response.status_code == 200:
                return True, response.url

        return False, None

    except requests.RequestException as e:
        logger.debug(f"URL check failed for {url}: {e}")
        return False, None


def _detect_page_type(url: str, html: str | None = None) -> IRPageType:
    """Detect the type of IR page from URL and content.

    Args:
        url: Page URL
        html: Optional HTML content for deeper analysis

    Returns:
        Detected page type
    """
    url_lower = url.lower()

    # Check URL patterns
    if any(p in url_lower for p in ["/calendar", "/schedule", "/event"]):
        return IRPageType.CALENDAR
    if any(p in url_lower for p in ["/news", "/release", "/whatsnew", "/topics"]):
        return IRPageType.NEWS
    if any(p in url_lower for p in ["/library", "/document", "/report"]):
        return IRPageType.LIBRARY
    if url_lower.endswith(("/ir/", "/ir", "/investor/", "/investors/")):
        return IRPageType.LANDING

    # Check HTML content for Japanese keywords
    if html:
        html_lower = html.lower()
        if any(
            kw in html_lower
            for kw in ["決算カレンダー", "決算発表予定", "irカレンダー", "earnings calendar"]
        ):
            return IRPageType.CALENDAR
        if any(kw in html_lower for kw in ["ir情報", "投資家情報", "investor relations"]):
            return IRPageType.LANDING

    return IRPageType.UNKNOWN


def _find_ir_link_in_html(html: str, base_url: str) -> str | None:
    """Find IR page link in HTML content using rule-based approach.

    Args:
        html: HTML content to search
        base_url: Base URL for resolving relative links

    Returns:
        IR page URL if found, None otherwise
    """
    soup = BeautifulSoup(html, HTML_PARSER)
    ir_keywords = extract_ir_keywords()

    # Search for links with IR-related text
    for link in soup.find_all("a", href=True):
        link_text = link.get_text(strip=True).lower()
        href = link["href"]

        # Check if link text contains IR keywords
        for keyword in ir_keywords:
            if keyword.lower() in link_text:
                # Resolve relative URL
                full_url = urljoin(base_url, href)
                # Validate it's not an anchor or javascript
                if full_url.startswith(("http://", "https://")):
                    logger.debug(f"Found IR link via keyword '{keyword}': {full_url}")
                    return full_url

    # Also check href patterns
    for link in soup.find_all("a", href=True):
        href = link["href"].lower()
        if any(p in href for p in ["/ir/", "/investor", "/ir.html"]):
            full_url = urljoin(base_url, link["href"])
            if full_url.startswith(("http://", "https://")):
                logger.debug(f"Found IR link via href pattern: {full_url}")
                return full_url

    return None


def _try_pattern_discovery(
    code: str, company_name: str | None, website: str, timeout: int | None,
) -> IRPageInfo | None:
    """Try to discover IR page via URL pattern matching."""
    candidates = get_candidate_urls(website, include_calendar=True, include_ir_landing=True)
    for url in candidates:
        exists, final_url = _check_url_exists(url, timeout=timeout)
        if exists and final_url:
            page_type = _detect_page_type(final_url)
            logger.info(f"Found IR page via pattern: {final_url}")
            return IRPageInfo(
                url=final_url,
                page_type=page_type,
                company_code=code,
                company_name=company_name,
                discovered_via="pattern",
            )
    return None


def _try_homepage_discovery(
    code: str, company_name: str | None, website: str, html: str, timeout: int | None,
) -> IRPageInfo | None:
    """Try to discover IR page by finding IR links in homepage HTML."""
    ir_link = _find_ir_link_in_html(html, website)
    if not ir_link:
        return None

    exists, final_url = _check_url_exists(ir_link, timeout=timeout)
    if exists and final_url:
        page_type = _detect_page_type(final_url)
        logger.info(f"Found IR page via homepage link: {final_url}")
        return IRPageInfo(
            url=final_url,
            page_type=page_type,
            company_code=code,
            company_name=company_name,
            discovered_via="homepage_link",
        )
    return None


def _try_llm_discovery(
    code: str,
    company_name: str | None,
    website: str,
    html: str,
    llm_client: LLMClient | None,
    timeout: int | None,
) -> IRPageInfo | None:
    """Try to discover IR page using LLM to find link in HTML."""
    if llm_client is None:
        llm_client = get_default_client()
    if not llm_client:
        return None

    logger.debug("Using LLM to find IR link")
    ir_link = llm_client.find_link(html, "IR page or Investor Relations page")
    if not ir_link:
        return None

    full_url = urljoin(website, ir_link)
    exists, final_url = _check_url_exists(full_url, timeout=timeout)
    if exists and final_url:
        page_type = _detect_page_type(final_url)
        logger.info(f"Found IR page via LLM: {final_url}")
        return IRPageInfo(
            url=final_url,
            page_type=page_type,
            company_code=code,
            company_name=company_name,
            discovered_via="llm",
        )
    return None


def discover_ir_page(
    code: str,
    llm_client: LLMClient | None = None,
    use_llm_fallback: bool = True,
    timeout: int | None = None,
) -> IRPageInfo | None:
    """Discover the IR page for a company.

    Flow:
    1. Get company website from pykabutan
    2. Try candidate URLs from patterns
    3. If not found, fetch homepage and search for IR link
    4. If still not found and LLM enabled, use LLM to find link

    Args:
        code: Stock code (e.g., "7203")
        llm_client: Optional LLM client for fallback discovery
        use_llm_fallback: Whether to use LLM as fallback (default True)
        timeout: Request timeout in seconds

    Returns:
        IRPageInfo if found, None otherwise
    """
    try:
        ticker = Ticker(code)
        profile = ticker.profile
        website = profile.website
        company_name = profile.name
    except (ValueError, AttributeError, requests.RequestException) as e:
        logger.warning(f"Failed to get company info for {code}: {e}")
        return None

    if not website:
        logger.info(f"No website found for {code}")
        return None

    logger.info(f"Discovering IR page for {code} ({company_name}): {website}")

    # Step 1: Try candidate URLs from patterns
    result = _try_pattern_discovery(code, company_name, website, timeout)
    if result:
        return result

    # Step 2: Fetch homepage and search for IR link
    logger.debug(f"Pattern matching failed, searching homepage for IR link")
    html = fetch_safe(website, timeout=timeout)
    if not html:
        logger.info(f"Could not discover IR page for {code}")
        return None

    result = _try_homepage_discovery(code, company_name, website, html, timeout)
    if result:
        return result

    # Step 3: Use LLM as fallback
    if use_llm_fallback:
        result = _try_llm_discovery(code, company_name, website, html, llm_client, timeout)
        if result:
            return result

    logger.info(f"Could not discover IR page for {code}")
    return None
