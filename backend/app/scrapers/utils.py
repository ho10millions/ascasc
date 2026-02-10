import asyncio
import logging
import random
from typing import Any

import aiohttp

from app.config import settings

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


def get_random_user_agent() -> str:
    return random.choice(USER_AGENTS)


def get_proxy() -> str | None:
    if settings.PROXY_URL and settings.PROXY_ROTATION_ENABLED:
        return settings.PROXY_URL
    return None


def parse_cookie_string(cookie_string: str) -> dict[str, str]:
    """Parse a raw cookie header string into a dict."""
    cookies = {}
    if not cookie_string:
        return cookies
    for pair in cookie_string.split(";"):
        pair = pair.strip()
        if "=" in pair:
            key, value = pair.split("=", 1)
            cookies[key.strip()] = value.strip()
    return cookies


async def fetch_json(
    url: str,
    headers: dict | None = None,
    params: dict | None = None,
    cookies: str | dict | None = None,
    max_retries: int = 3,
    delay: float = 1.0,
) -> Any:
    """Fetch JSON from URL with retry logic and anti-detection headers."""
    default_headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if headers:
        default_headers.update(headers)

    jar = None
    if cookies:
        cookie_dict = parse_cookie_string(cookies) if isinstance(cookies, str) else cookies
        jar = aiohttp.CookieJar(unsafe=True)

    proxy = get_proxy()

    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession(cookie_jar=jar) as session:
                if cookies:
                    cookie_dict = parse_cookie_string(cookies) if isinstance(cookies, str) else cookies
                    for name, value in cookie_dict.items():
                        session.cookie_jar.update_cookies({name: value})
                async with session.get(
                    url,
                    headers=default_headers,
                    params=params,
                    proxy=proxy,
                    timeout=aiohttp.ClientTimeout(total=30),
                    ssl=False,
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:
                        wait = delay * (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(f"Rate limited on {url}, waiting {wait:.1f}s")
                        await asyncio.sleep(wait)
                    else:
                        logger.warning(f"HTTP {response.status} from {url}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(delay * (attempt + 1))
        except Exception as e:
            logger.error(f"Request error for {url}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(delay * (attempt + 1))

    return None


async def fetch_html(
    url: str,
    headers: dict | None = None,
    max_retries: int = 3,
    delay: float = 1.0,
) -> str | None:
    """Fetch raw HTML from URL."""
    default_headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if headers:
        default_headers.update(headers)

    proxy = get_proxy()

    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=default_headers,
                    proxy=proxy,
                    timeout=aiohttp.ClientTimeout(total=30),
                    ssl=False,
                ) as response:
                    if response.status == 200:
                        return await response.text()
                    elif response.status == 429:
                        wait = delay * (2 ** attempt) + random.uniform(0, 1)
                        await asyncio.sleep(wait)
                    else:
                        if attempt < max_retries - 1:
                            await asyncio.sleep(delay * (attempt + 1))
        except Exception as e:
            logger.error(f"Request error for {url}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(delay * (attempt + 1))

    return None


async def fetch_with_playwright(
    url: str,
    wait_selector: str | None = None,
    wait_time: int = 3000,
) -> str | None:
    """Fetch page content using Playwright for JS-rendered pages."""
    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=get_random_user_agent(),
                viewport={"width": 1920, "height": 1080},
            )
            page = await context.new_page()

            await page.goto(url, wait_until="networkidle", timeout=30000)

            if wait_selector:
                await page.wait_for_selector(wait_selector, timeout=10000)
            else:
                await page.wait_for_timeout(wait_time)

            content = await page.content()
            await browser.close()
            return content
    except Exception as e:
        logger.error(f"Playwright error for {url}: {e}")
        return None


def classify_item_type(market_hash_name: str) -> str | None:
    """Guess item type from its Steam market hash name."""
    name_lower = market_hash_name.lower()

    if name_lower.startswith("★"):
        if "karambit" in name_lower or "knife" in name_lower or "bayonet" in name_lower:
            return "Knife"
        if "gloves" in name_lower or "wraps" in name_lower:
            return "Gloves"
        return "Knife"

    type_keywords = {
        "ak-47": "Rifle", "m4a4": "Rifle", "m4a1-s": "Rifle", "awp": "Sniper Rifle",
        "desert eagle": "Pistol", "usp-s": "Pistol", "glock-18": "Pistol", "p250": "Pistol",
        "sticker": "Sticker", "case": "Container", "key": "Key",
        "music kit": "Music Kit", "agent": "Agent", "patch": "Patch",
        "mp9": "SMG", "mac-10": "SMG", "ump-45": "SMG", "p90": "SMG",
        "ssg 08": "Sniper Rifle", "scar-20": "Sniper Rifle", "g3sg1": "Sniper Rifle",
        "nova": "Shotgun", "xm1014": "Shotgun", "mag-7": "Shotgun",
        "negev": "Machine Gun", "m249": "Machine Gun",
        "five-seven": "Pistol", "tec-9": "Pistol", "cz75-auto": "Pistol", "r8 revolver": "Pistol",
    }

    for keyword, item_type in type_keywords.items():
        if keyword in name_lower:
            return item_type

    return None
