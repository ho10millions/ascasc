import os
from dataclasses import dataclass


@dataclass
class Config:
    # Telegram Bot Token (get from @BotFather)
    BOT_TOKEN: str = os.environ.get("BOT_TOKEN", "")

    # Admin Telegram user IDs (can approve payments)
    # Comma-separated list of IDs: "123456,789012"
    ADMIN_IDS: list[int] = None

    # Payment details shown to users
    PAYMENT_BANK: str = os.environ.get("PAYMENT_BANK", "Сбербанк")
    PAYMENT_CARD: str = os.environ.get("PAYMENT_CARD", "4276 1234 5678 9012")
    PAYMENT_HOLDER: str = os.environ.get("PAYMENT_HOLDER", "Иванова Анна Сергеевна")

    # Prices for each period (in RUB)
    PRICE_1MIN: int = int(os.environ.get("PRICE_1MIN", "10"))
    PRICE_WEEK: int = int(os.environ.get("PRICE_WEEK", "1000"))
    PRICE_MONTH: int = int(os.environ.get("PRICE_MONTH", "3000"))
    PRICE_3MONTHS: int = int(os.environ.get("PRICE_3MONTHS", "7500"))

    # Bot username (without @)
    BOT_USERNAME: str = os.environ.get("BOT_USERNAME", "AsiaVipmassage_bot")

    # Database path
    DB_PATH: str = os.environ.get("DB_PATH", "bot/private_bot.db")

    def __post_init__(self):
        if self.ADMIN_IDS is None:
            raw = os.environ.get("ADMIN_IDS", "")
            if raw:
                self.ADMIN_IDS = [int(x.strip()) for x in raw.split(",") if x.strip()]
            else:
                self.ADMIN_IDS = []


config = Config()
