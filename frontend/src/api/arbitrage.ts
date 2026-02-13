import client from "./client";
import type { ArbitrageFilters, ArbitrageOpportunity, ArbitrageStats, PaginatedResponse } from "../types";

export async function getArbitrageOpportunities(
  filters: Partial<ArbitrageFilters>
): Promise<PaginatedResponse<ArbitrageOpportunity>> {
  const params: Record<string, string | number> = {};
  if (filters.min_profit_pct !== undefined) params.min_profit_pct = filters.min_profit_pct;
  if (filters.max_profit_pct !== undefined) params.max_profit_pct = filters.max_profit_pct;
  if (filters.game) params.game = filters.game;
  if (filters.item_type) params.item_type = filters.item_type;
  if (filters.min_price !== undefined) params.min_price = filters.min_price;
  if (filters.max_price !== undefined) params.max_price = filters.max_price;
  if (filters.marketplace_slug) params.marketplace_slug = filters.marketplace_slug;
  if (filters.buy_marketplace_slug) params.buy_marketplace_slug = filters.buy_marketplace_slug;
  if (filters.sell_marketplace_slug) params.sell_marketplace_slug = filters.sell_marketplace_slug;
  if (filters.search) params.search = filters.search;
  if (filters.sort_by) params.sort_by = filters.sort_by;
  if (filters.sort_order) params.sort_order = filters.sort_order;
  if (filters.page) params.page = filters.page;
  if (filters.per_page) params.per_page = filters.per_page;

  const { data } = await client.get<PaginatedResponse<ArbitrageOpportunity>>("/arbitrage", { params });
  return data;
}

export async function getArbitrageStats(): Promise<ArbitrageStats> {
  const { data } = await client.get<ArbitrageStats>("/arbitrage/stats");
  return data;
}
