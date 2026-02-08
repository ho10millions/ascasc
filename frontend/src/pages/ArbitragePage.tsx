import { useQuery } from "@tanstack/react-query";
import { useFilterStore } from "../stores/filterStore";
import { getArbitrageOpportunities } from "../api/arbitrage";
import { getMarketplaces } from "../api/admin";
import { Search, SlidersHorizontal, ExternalLink } from "lucide-react";
import clsx from "clsx";

function formatUSD(value: number): string {
  return `$${value.toFixed(2)}`;
}

export default function ArbitragePage() {
  const filters = useFilterStore();
  const { setFilter } = filters;

  const { data: marketplaces } = useQuery({
    queryKey: ["marketplaces"],
    queryFn: getMarketplaces,
  });

  const { data, isLoading } = useQuery({
    queryKey: [
      "arbitrage",
      filters.minProfitPct,
      filters.game,
      filters.itemType,
      filters.minPrice,
      filters.maxPrice,
      filters.marketplaceSlug,
      filters.search,
      filters.sortBy,
      filters.sortOrder,
      filters.page,
      filters.perPage,
    ],
    queryFn: () =>
      getArbitrageOpportunities({
        min_profit_pct: filters.minProfitPct,
        game: filters.game || undefined,
        item_type: filters.itemType || undefined,
        min_price: filters.minPrice,
        max_price: filters.maxPrice,
        marketplace_slug: filters.marketplaceSlug || undefined,
        search: filters.search || undefined,
        sort_by: filters.sortBy,
        sort_order: filters.sortOrder,
        page: filters.page,
        per_page: filters.perPage,
      }),
    refetchInterval: 60_000,
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Arbitrage Opportunities</h1>
          <p className="text-dark-400 mt-1">
            {data?.total ?? 0} opportunities found
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <SlidersHorizontal size={18} className="text-dark-400" />
          <h3 className="font-medium">Filters</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-4">
          <div>
            <label className="block text-xs text-dark-400 mb-1">Search</label>
            <div className="relative">
              <Search size={16} className="absolute left-3 top-2.5 text-dark-500" />
              <input
                type="text"
                value={filters.search}
                onChange={(e) => setFilter("search", e.target.value)}
                placeholder="Item name..."
                className="input w-full pl-9 text-sm"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs text-dark-400 mb-1">
              Min Profit: {filters.minProfitPct}%
            </label>
            <input
              type="range"
              min={0}
              max={200}
              value={filters.minProfitPct}
              onChange={(e) => setFilter("minProfitPct", Number(e.target.value))}
              className="w-full accent-primary-500"
            />
          </div>

          <div>
            <label className="block text-xs text-dark-400 mb-1">Game</label>
            <select
              value={filters.game}
              onChange={(e) => setFilter("game", e.target.value)}
              className="input w-full text-sm"
            >
              <option value="">All Games</option>
              <option value="cs2">CS2</option>
              <option value="dota2">Dota 2</option>
              <option value="tf2">TF2</option>
              <option value="rust">Rust</option>
            </select>
          </div>

          <div>
            <label className="block text-xs text-dark-400 mb-1">Item Type</label>
            <select
              value={filters.itemType}
              onChange={(e) => setFilter("itemType", e.target.value)}
              className="input w-full text-sm"
            >
              <option value="">All Types</option>
              <option value="Knife">Knife</option>
              <option value="Gloves">Gloves</option>
              <option value="Rifle">Rifle</option>
              <option value="Pistol">Pistol</option>
              <option value="SMG">SMG</option>
              <option value="Sniper Rifle">Sniper Rifle</option>
              <option value="Sticker">Sticker</option>
              <option value="Container">Case</option>
            </select>
          </div>

          <div>
            <label className="block text-xs text-dark-400 mb-1">Marketplace</label>
            <select
              value={filters.marketplaceSlug}
              onChange={(e) => setFilter("marketplaceSlug", e.target.value)}
              className="input w-full text-sm"
            >
              <option value="">All</option>
              {marketplaces
                ?.filter((m) => m.slug !== "steam")
                .map((m) => (
                  <option key={m.slug} value={m.slug}>
                    {m.name}
                  </option>
                ))}
            </select>
          </div>

          <div>
            <label className="block text-xs text-dark-400 mb-1">Sort By</label>
            <select
              value={filters.sortBy}
              onChange={(e) => setFilter("sortBy", e.target.value)}
              className="input w-full text-sm"
            >
              <option value="profit_pct">Profit %</option>
              <option value="profit_usd">Profit $</option>
              <option value="buy_price">Buy Price</option>
              <option value="steam_price">Steam Price</option>
              <option value="name">Name</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="card overflow-x-auto p-0">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-dark-700">
              <th className="text-left px-4 py-3 text-dark-400 font-medium">Item</th>
              <th className="text-left px-4 py-3 text-dark-400 font-medium">Game</th>
              <th className="text-right px-4 py-3 text-dark-400 font-medium">Buy Price</th>
              <th className="text-left px-4 py-3 text-dark-400 font-medium">Marketplace</th>
              <th className="text-right px-4 py-3 text-dark-400 font-medium">Steam (net)</th>
              <th className="text-right px-4 py-3 text-dark-400 font-medium">Profit</th>
              <th className="text-center px-4 py-3 text-dark-400 font-medium">Link</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={7} className="text-center py-12 text-dark-400">
                  Loading...
                </td>
              </tr>
            ) : !data?.items.length ? (
              <tr>
                <td colSpan={7} className="text-center py-12 text-dark-400">
                  No opportunities found. Adjust your filters.
                </td>
              </tr>
            ) : (
              data.items.map((opp) => (
                <tr
                  key={opp.id}
                  className={clsx(
                    "border-b border-dark-800 hover:bg-dark-800/50 transition-colors",
                    opp.profit_pct >= 50 && "bg-yellow-900/10"
                  )}
                >
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      {opp.icon_url && (
                        <img
                          src={opp.icon_url}
                          alt=""
                          className="w-8 h-8 rounded object-contain bg-dark-800"
                        />
                      )}
                      <span className="font-medium truncate max-w-[250px]" title={opp.market_hash_name}>
                        {opp.market_hash_name}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-xs bg-dark-700 px-2 py-1 rounded uppercase">
                      {opp.game}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-mono">
                    {formatUSD(opp.buy_price_usd)}
                  </td>
                  <td className="px-4 py-3 text-dark-300">{opp.buy_marketplace_name}</td>
                  <td className="px-4 py-3 text-right font-mono text-dark-300">
                    {formatUSD(opp.steam_price_after_fee)}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span
                      className={clsx(
                        opp.profit_pct >= 50 ? "badge-high-profit" : "badge-profit"
                      )}
                    >
                      +{opp.profit_pct.toFixed(1)}%
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <a
                      href={opp.buy_marketplace_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary-400 hover:text-primary-300"
                    >
                      <ExternalLink size={16} />
                    </a>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => setFilter("page", Math.max(1, filters.page - 1))}
            disabled={filters.page <= 1}
            className="btn-secondary text-sm disabled:opacity-50"
          >
            Previous
          </button>
          <span className="text-dark-400 text-sm">
            Page {filters.page} of {data.total_pages}
          </span>
          <button
            onClick={() => setFilter("page", Math.min(data.total_pages, filters.page + 1))}
            disabled={filters.page >= data.total_pages}
            className="btn-secondary text-sm disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
