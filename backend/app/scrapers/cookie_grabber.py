"""
Cookie grabber — opens a real browser so you can log in manually.
After login, cookies are saved to .env automatically.

Usage:
    python -m app.scrapers.cookie_grabber cs-money
    python -m app.scrapers.cookie_grabber buff163
    python -m app.scrapers.cookie_grabber all
"""

import argparse
import os
import sys
import tempfile

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

try:
    from webdriver_manager.chrome import ChromeDriverManager
    HAS_WDM = True
except ImportError:
    HAS_WDM = False

# Marketplace configs: slug -> (url, env_var_name)
MARKETPLACES = {
    "cs-money": {
        "url": "https://cs.money/",
        "env_var": "CS_MONEY_COOKIES",
        "name": "CS.Money",
    },
    "buff163": {
        "url": "https://buff.163.com/",
        "env_var": "BUFF163_COOKIES",
        "name": "Buff163",
    },
}

ENV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")


def get_chrome_driver() -> webdriver.Chrome:
    """Create a Chrome driver with visible window for manual login."""
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Use temp dir for Chrome profile to avoid System32 permission issues
    user_data_dir = os.path.join(tempfile.gettempdir(), "scrooge_chrome_profile")
    options.add_argument(f"--user-data-dir={user_data_dir}")

    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # Try to find Chrome binary
    chrome_paths = [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
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

    # Hide webdriver flag from detection
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


def grab_cookies(slug: str) -> None:
    """Open browser for a marketplace, wait for login, grab cookies."""
    mp = MARKETPLACES[slug]
    print(f"\n{'='*50}")
    print(f"  {mp['name']} — Cookie Grabber")
    print(f"{'='*50}")
    print(f"\n1. Сейчас откроется браузер на {mp['url']}")
    print("2. Залогинься в свой аккаунт")
    print("3. Когда будешь залогинен — вернись сюда и нажми ENTER")
    print()

    driver = get_chrome_driver()
    try:
        driver.get(mp["url"])
        input(f">>> Нажми ENTER когда залогинишься на {mp['name']}... ")

        cookies = driver.get_cookies()
        if not cookies:
            print("Куки не найдены. Попробуй ещё раз.")
            return

        cookie_string = cookies_to_string(cookies)
        update_env_file(mp["env_var"], cookie_string)

        print(f"\nСохранено {len(cookies)} куки в .env ({mp['env_var']})")
        print(f"Куки: {cookie_string[:80]}...")
    finally:
        driver.quit()


def main():
    parser = argparse.ArgumentParser(description="Grab marketplace cookies via browser login")
    parser.add_argument(
        "marketplace",
        choices=list(MARKETPLACES.keys()) + ["all"],
        help="Which marketplace to grab cookies for",
    )
    args = parser.parse_args()

    if args.marketplace == "all":
        for slug in MARKETPLACES:
            grab_cookies(slug)
    else:
        grab_cookies(args.marketplace)

    print("\nГотово! Куки сохранены в .env")
    print("Теперь скраперы будут использовать авторизованную сессию.")


if __name__ == "__main__":
    main()
