"""Scraper registry — maps marketplace slugs to scraper classes."""

from app.scrapers.base import BaseScraper
from app.scrapers.steam.steam_market import SteamMarketScraper
from app.scrapers.marketplaces.skinswap import SkinSwapScraper
from app.scrapers.marketplaces.shadowpay import ShadowPayScraper
from app.scrapers.marketplaces.skins_cash import SkinsCashScraper
from app.scrapers.marketplaces.white_market import WhiteMarketScraper
from app.scrapers.marketplaces.waxpeer import WaxpeerScraper
from app.scrapers.marketplaces.lis_skins import LisSkinsScraper
from app.scrapers.marketplaces.skinomat import SkinomatScraper
from app.scrapers.marketplaces.aim_market import AimMarketScraper
from app.scrapers.marketplaces.avan_market import AvanMarketScraper
from app.scrapers.marketplaces.pirateswap import PirateSwapScraper
from app.scrapers.marketplaces.moon_market import MoonMarketScraper
from app.scrapers.marketplaces.skin_place import SkinPlaceScraper
from app.scrapers.marketplaces.cs_money import CSMoneyScraper
from app.scrapers.marketplaces.skin_land import SkinLandScraper
from app.scrapers.marketplaces.csfloat import CSFloatScraper
from app.scrapers.marketplaces.itrade_gg import ITradeScraper
from app.scrapers.marketplaces.dmarket import DMarketScraper
from app.scrapers.marketplaces.skins_com import SkinsComScraper
from app.scrapers.marketplaces.skincashier import SkinCashierScraper
from app.scrapers.marketplaces.swap_gg import SwapGGScraper
from app.scrapers.marketplaces.buff_market import BuffMarketScraper
from app.scrapers.marketplaces.market_csgo import MarketCSGOScraper
from app.scrapers.marketplaces.buff163 import Buff163Scraper
from app.scrapers.marketplaces.cs_trade import CSTradeScraper
from app.scrapers.marketplaces.loot_farm import LootFarmScraper
from app.scrapers.marketplaces.skincantor import SkinCantorScraper
from app.scrapers.marketplaces.skinout_gg import SkinoutScraper
from app.scrapers.marketplaces.youpin898 import Youpin898Scraper
from app.scrapers.marketplaces.rapidskins import RapidSkinsScraper

SCRAPER_REGISTRY: dict[str, type[BaseScraper]] = {
    "steam": SteamMarketScraper,
    "skinswap": SkinSwapScraper,
    "shadowpay": ShadowPayScraper,
    "skins-cash": SkinsCashScraper,
    "white-market": WhiteMarketScraper,
    "waxpeer": WaxpeerScraper,
    "lis-skins": LisSkinsScraper,
    "skinomat": SkinomatScraper,
    "aim-market": AimMarketScraper,
    "avan-market": AvanMarketScraper,
    "pirateswap": PirateSwapScraper,
    "moon-market": MoonMarketScraper,
    "skin-place": SkinPlaceScraper,
    "cs-money": CSMoneyScraper,
    "skin-land": SkinLandScraper,
    "csfloat": CSFloatScraper,
    "itrade-gg": ITradeScraper,
    "dmarket": DMarketScraper,
    "skins-com": SkinsComScraper,
    "skincashier": SkinCashierScraper,
    "swap-gg": SwapGGScraper,
    "buff-market": BuffMarketScraper,
    "market-csgo": MarketCSGOScraper,
    "buff163": Buff163Scraper,
    "cs-trade": CSTradeScraper,
    "loot-farm": LootFarmScraper,
    "skincantor": SkinCantorScraper,
    "skinout-gg": SkinoutScraper,
    "youpin898": Youpin898Scraper,
    "rapidskins": RapidSkinsScraper,
}


def get_scraper(slug: str) -> BaseScraper | None:
    """Get a scraper instance by marketplace slug."""
    scraper_cls = SCRAPER_REGISTRY.get(slug)
    if scraper_cls:
        return scraper_cls()
    return None


def get_all_scrapers() -> list[tuple[str, BaseScraper]]:
    """Get all registered scrapers."""
    return [(slug, cls()) for slug, cls in SCRAPER_REGISTRY.items()]
