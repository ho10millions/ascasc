import client from "./client";
import type { Item, ItemPriceComparison, PaginatedResponse } from "../types";

export async function getItems(params: {
  game?: string;
  item_type?: string;
  search?: string;
  page?: number;
  per_page?: number;
}): Promise<PaginatedResponse<Item>> {
  const { data } = await client.get<PaginatedResponse<Item>>("/items", { params });
  return data;
}

export async function getItem(itemId: string): Promise<Item> {
  const { data } = await client.get<Item>(`/items/${itemId}`);
  return data;
}

export async function getItemPrices(itemId: string): Promise<ItemPriceComparison> {
  const { data } = await client.get<ItemPriceComparison>(`/items/${itemId}/prices`);
  return data;
}
