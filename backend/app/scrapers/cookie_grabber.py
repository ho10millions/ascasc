"""
Cookie grabber — reads cookies directly from Chrome's database.
No Selenium needed, no browser opening, just reads your existing cookies.

Usage:
    python -m app.scrapers.cookie_grabber cs-money
    python -m app.scrapers.cookie_grabber buff163
    python -m app.scrapers.cookie_grabber all
"""

import argparse
import os
import sys

try:
    import browser_cookie3
except ImportError:
    print("Установи browser_cookie3:")
    print("  pip install browser-cookie3")
    sys.exit(1)

# Marketplace configs
MARKETPLACES = {
    "cs-money": {
        "domain": ".cs.money",
        "env_var": "CS_MONEY_COOKIES",
        "name": "CS.Money",
    },
    "buff163": {
        "domain": ".163.com",
        "env_var": "BUFF163_COOKIES",
        "name": "Buff163",
    },
}

ENV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")


def cookies_to_string(cookie_jar, domain: str) -> str:
    """Extract cookies for a specific domain and convert to header string."""
    pairs = []
    for cookie in cookie_jar:
        if domain in cookie.domain:
            pairs.append(f"{cookie.name}={cookie.value}")
    return "; ".join(pairs)


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
    """Read cookies from Chrome for a marketplace."""
    mp = MARKETPLACES[slug]
    print(f"\n{'='*50}")
    print(f"  {mp['name']} — Cookie Grabber")
    print(f"{'='*50}")
    print(f"\nЧитаем куки из Chrome для {mp['domain']}...")

    try:
        cookie_jar = browser_cookie3.chrome(domain_name=mp["domain"])
    except Exception as e:
        print(f"Ошибка чтения куки: {e}")
        print("Убедись что Chrome установлен и ты залогинен на сайте.")
        return

    cookie_string = cookies_to_string(cookie_jar, mp["domain"])

    if not cookie_string:
        print(f"Куки для {mp['domain']} не найдены.")
        print(f"Зайди на {mp['name']} в Chrome и залогинься, потом запусти снова.")
        return

    update_env_file(mp["env_var"], cookie_string)

    # Count cookies and check for auth
    cookie_count = cookie_string.count("=")
    has_auth = any(
        key in cookie_string
        for key in ["csgo_ses", "steamid", "session", "cf_clearance"]
    )

    print(f"\nСохранено ~{cookie_count} куки в .env ({mp['env_var']})")
    if has_auth:
        print("Авторизованная сессия найдена!")
    else:
        print("Сессионные куки не найдены — возможно ты не залогинен на сайте")


def main():
    parser = argparse.ArgumentParser(
        description="Read marketplace cookies directly from Chrome"
    )
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
    print("Скраперы будут использовать авторизованную сессию.")


if __name__ == "__main__":
    main()
