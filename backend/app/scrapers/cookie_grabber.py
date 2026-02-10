"""
Cookie grabber — extracts cookies from your real Chrome profile.
No manual login needed if you're already logged in to Chrome.

Usage:
    python -m app.scrapers.cookie_grabber cs-money
    python -m app.scrapers.cookie_grabber buff163
    python -m app.scrapers.cookie_grabber all
    python -m app.scrapers.cookie_grabber cs-money --refresh
        (auto-refresh: opens cs.money to refresh cookies, then saves)

First run:
    1. CLOSE Chrome completely (important!)
    2. Run the script — it opens Chrome with YOUR profile
    3. You're already logged in (cookies from your browser)
    4. Press Enter — cookies saved to .env

After that, cookies stay fresh as long as you use Chrome normally.
Use --refresh to auto-refresh without interaction.
"""

import argparse
import os
import platform
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

try:
    from webdriver_manager.chrome import ChromeDriverManager
    HAS_WDM = True
except ImportError:
    HAS_WDM = False

# Marketplace configs
MARKETPLACES = {
    "cs-money": {
        "url": "https://cs.money/market/buy/",
        "env_var": "CS_MONEY_COOKIES",
        "name": "CS.Money",
    },
    "buff163": {
        "url": "https://buff.163.com/market/csgo",
        "env_var": "BUFF163_COOKIES",
        "name": "Buff163",
    },
}

ENV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")


def find_chrome_profile_dir() -> str | None:
    """Find the default Chrome user data directory for the current OS."""
    system = platform.system()
    if system == "Windows":
        path = os.path.expandvars(r"%LocalAppData%\Google\Chrome\User Data")
    elif system == "Darwin":
        path = os.path.expanduser("~/Library/Application Support/Google/Chrome")
    else:  # Linux
        path = os.path.expanduser("~/.config/google-chrome")

    if os.path.exists(path):
        return path
    return None


def get_chrome_driver(use_profile: bool = True) -> webdriver.Chrome:
    """Create Chrome driver, optionally using the real user profile."""
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    if use_profile:
        profile_dir = find_chrome_profile_dir()
        if profile_dir:
            options.add_argument(f"--user-data-dir={profile_dir}")
            options.add_argument("--profile-directory=Default")
            print(f"Используем Chrome профиль: {profile_dir}")
        else:
            print("Chrome профиль не найден, используем временный")

    # Try to find Chrome binary
    chrome_paths = [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ]
    for path in chrome_paths:
        if os.path.exists(path):
            options.binary_location = path
            break

    if HAS_WDM:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    else:
        driver = webdriver.Chrome(options=options)

    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
    )
    return driver


def cookies_to_string(cookies: list[dict]) -> str:
    """Convert Selenium cookie list to a Cookie header string."""
    return "; ".join(f"{c['name']}={c['value']}" for c in cookies)


def update_env_file(env_var: str, value: str) -> None:
    """Update or add a variable in the .env file."""
    env_path = os.path.normpath(ENV_PATH)

    lines = []
    found = False
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

    new_lines = []
    for line in lines:
        if line.startswith(f"{env_var}="):
            new_lines.append(f"{env_var}={value}\n")
            found = True
        else:
            new_lines.append(line)

    if not found:
        new_lines.append(f"{env_var}={value}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)


def grab_cookies(slug: str, auto_refresh: bool = False) -> None:
    """Extract cookies from Chrome profile for a marketplace."""
    mp = MARKETPLACES[slug]
    print(f"\n{'='*50}")
    print(f"  {mp['name']} — Cookie Grabber")
    print(f"{'='*50}")

    if not auto_refresh:
        print(f"\n⚠  Закрой Chrome полностью перед запуском!")
        print(f"   (Selenium не может открыть профиль если Chrome уже запущен)")
        print()
        input(">>> Закрыл Chrome? Жми ENTER... ")

    print(f"\nОткрываем {mp['url']} с твоим Chrome профилем...")
    driver = get_chrome_driver(use_profile=True)
    try:
        driver.get(mp["url"])

        if auto_refresh:
            # Wait for page to load and cookies to be set
            print("Ждём загрузку страницы (10 сек)...")
            time.sleep(10)
        else:
            print(f"\nПроверь что ты залогинен на {mp['name']}")
            print("(Если ты уже залогинен в Chrome — всё ок, просто жми Enter)")
            input(f"\n>>> Нажми ENTER для сохранения куки... ")

        cookies = driver.get_cookies()
        if not cookies:
            print("Куки не найдены!")
            return

        cookie_string = cookies_to_string(cookies)
        update_env_file(mp["env_var"], cookie_string)

        # Check if we got auth cookies
        cookie_names = [c["name"] for c in cookies]
        has_session = any(
            name in cookie_names
            for name in ["csgo_ses", "steamid", "session", "cf_clearance"]
        )

        print(f"\nСохранено {len(cookies)} куки в .env ({mp['env_var']})")
        if has_session:
            print("Авторизованная сессия найдена!")
        else:
            print("Сессионные куки не найдены — возможно ты не залогинен")

    finally:
        driver.quit()


def main():
    parser = argparse.ArgumentParser(
        description="Extract marketplace cookies from your Chrome profile"
    )
    parser.add_argument(
        "marketplace",
        choices=list(MARKETPLACES.keys()) + ["all"],
        help="Which marketplace to grab cookies for",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Auto-refresh mode: no interaction needed",
    )
    args = parser.parse_args()

    if args.marketplace == "all":
        for slug in MARKETPLACES:
            grab_cookies(slug, auto_refresh=args.refresh)
    else:
        grab_cookies(args.marketplace, auto_refresh=args.refresh)

    print("\nГотово! Куки сохранены в .env")
    print("Скраперы будут использовать авторизованную сессию.")


if __name__ == "__main__":
    main()
