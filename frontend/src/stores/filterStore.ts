import { create } from "zustand";

interface FilterState {
  minProfitPct: number;
  maxProfitPct: number | undefined;
  game: string;
  itemType: string;
  minPrice: number | undefined;
  maxPrice: number | undefined;
  marketplaceSlug: string;
  search: string;
  sortBy: string;
  sortOrder: string;
  page: number;
  perPage: number;
  setFilter: (key: string, value: any) => void;
  resetFilters: () => void;
}

const defaults = {
  minProfitPct: 0,
  maxProfitPct: undefined as number | undefined,
  game: "",
  itemType: "",
  minPrice: undefined as number | undefined,
  maxPrice: undefined as number | undefined,
  marketplaceSlug: "",
  search: "",
  sortBy: "profit_pct",
  sortOrder: "desc",
  page: 1,
  perPage: 50,
};

export const useFilterStore = create<FilterState>((set) => ({
  ...defaults,
  setFilter: (key, value) => set((state) => ({ ...state, [key]: value, page: key === "page" ? value : 1 })),
  resetFilters: () => set(defaults),
}));
