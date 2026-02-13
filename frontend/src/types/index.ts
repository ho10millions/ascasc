export interface User {
  id: string;
  username: string;
  email: string;
  is_admin: boolean;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface Item {
  id: string;
  game: string;
  market_hash_name: string;
  icon_url: string | null;
  item_type: string | null;
  rarity: string | null;
  created_at: string;
}

export interface ArbitrageOpportunity {
  id: number;
  item_id: string;
  market_hash_name: string;
  game: string;
  icon_url: string | null;
  item_type: string | null;
  buy_marketplace_name: string;
  buy_marketplace_slug: string;
  buy_marketplace_url: string;
  sell_marketplace_name: string;
  sell_marketplace_slug: string;
  sell_marketplace_url: string;
  buy_marketplace_fee_pct: number;
  sell_marketplace_fee_pct: number;
  buy_price_usd: number;
  sell_price_usd: number;
  sell_price_after_fee: number;
  profit_usd: number;
  profit_pct: number;
  is_active: boolean;
  detected_at: string;
}

export interface Marketplace {
  id: number;
  name: string;
  slug: string;
  base_url: string;
  scraper_type: string;
  is_enabled: boolean;
  scrape_interval_minutes: number;
  last_scraped_at: string | null;
}

export interface PriceComparisonEntry {
  marketplace_name: string;
  marketplace_slug: string;
  price_usd: number;
  listing_count: number | null;
  scraped_at: string;
  marketplace_url: string;
}

export interface ItemPriceComparison {
  item_id: string;
  market_hash_name: string;
  game: string;
  steam_price: number | null;
  steam_price_after_fee: number | null;
  prices: PriceComparisonEntry[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface ArbitrageStats {
  active_opportunities: number;
  high_value_opportunities: number;
  avg_profit_pct: number;
  max_profit_pct: number;
  total_items_tracked: number;
}

export interface InviteCode {
  id: string;
  code: string;
  max_uses: number;
  times_used: number;
  is_active: boolean;
  grants_admin: boolean;
  expires_at: string | null;
  created_at: string;
}

export interface ScrapeJob {
  id: string;
  marketplace_id: number;
  status: string;
  items_scraped: number;
  errors: Record<string, string> | null;
  triggered_by: string;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
}

export interface ArbitrageFilters {
  min_profit_pct: number;
  max_profit_pct?: number;
  game?: string;
  item_type?: string;
  min_price?: number;
  max_price?: number;
  marketplace_slug?: string;
  buy_marketplace_slug?: string;
  sell_marketplace_slug?: string;
  search?: string;
  sort_by: string;
  sort_order: string;
  page: number;
  per_page: number;
}
