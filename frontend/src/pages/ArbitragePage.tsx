import { useQuery } from "@tanstack/react-query";
import { useFilterStore } from "../stores/filterStore";
import { getArbitrageOpportunities } from "../api/arbitrage";
import { getMarketplaces } from "../api/admin";
import { Search, SlidersHorizontal, ExternalLink, TrendingUp, ChevronLeft, ChevronRight, Radio, Clock, Loader2, CheckCircle2, XCircle, ArrowRight } from "lucide-react";
import clsx from "clsx";

function formatUSD(value: number): string {
  return `$${value.toFixed(2)}`;
}

function timeAgo(isoString: string): string {
  const diff = Date.now() - new Date(isoString).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ${mins % 60}m ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export default function ArbitragePage() {
  const filters = useFilterStore();
  const { setFilter } = filters;

  const { data: scraperStatus } = useQuery({
    queryKey: ["scraper-status"],
    queryFn: async () => {
      const res = await fetch("/api/v1/scraper-status");
      return res.json();
    },
    refetchInterval: 5_000,
  });

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
      filters.buyMarketplaceSlug,
      filters.sellMarketplaceSlug,
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
        buy_marketplace_slug: filters.buyMarketplaceSlug || undefined,
        sell_marketplace_slug: filters.sellMarketplaceSlug || undefined,
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
      {/* Header */}
      <div className="flex items-center justify-between animate-fade-in">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-primary-500/10">
              <TrendingUp size={22} className="text-primary-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">Arbitrage</h1>
              <p className="text-dark-400 text-sm mt-0.5">
                <span className="text-primary-400 font-semibold">{data?.total ?? 0}</span> opportunities found
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Scraper Status Widget */}
      {scraperStatus && (
        <div className="card animate-slide-up flex items-center justify-between gap-4 py-3 px-5">
          <div className="flex items-center gap-3">
            {scraperStatus.running ? (
              <>
                <div className="relative">
                  <Loader2 size={18} className="text-primary-400 animate-spin" />
                  <div className="absolute inset-0 bg-primary-400/20 rounded-full animate-ping" />
                </div>
                <div>
                  <span className="text-sm font-medium text-primary-400">Scraper active</span>
                  {scraperStatus.current_marketplace && (
                    <span className="text-dark-400 text-xs ml-2">
                      Scanning <span className="text-dark-300 font-medium">{scraperStatus.current_marketplace}</span>...
                    </span>
                  )}
                </div>
              </>
            ) : (
              <>
                <Radio size={16} className="text-dark-500" />
                <span className="text-sm text-dark-400">Scraper idle</span>
              </>
            )}
          </div>

          <div className="flex items-center gap-4 text-xs">
            {scraperStatus.last_run && (
              <div className="flex items-center gap-1.5 text-dark-400">
                <Clock size={12} />
                <span>Last run: <span className="text-dark-300 font-mono">{timeAgo(scraperStatus.last_run)}</span></span>
              </div>
            )}
            {scraperStatus.last_result && (
              <div className="flex items-center gap-1.5">
                {scraperStatus.last_result === "success" ? (
                  <CheckCircle2 size={12} className="text-emerald-400" />
                ) : (
                  <XCircle size={12} className="text-red-400" />
                )}
                <span className={clsx(
                  "font-medium",
                  scraperStatus.last_result === "success" ? "text-emerald-400" : "text-red-400"
                )} title={scraperStatus.last_result !== "success" ? scraperStatus.last_result : undefined}>
                  {scraperStatus.last_result === "success"
                    ? "Success"
                    : scraperStatus.last_result.replace("error: ", "").slice(0, 80) || "Error"}
                </span>
              </div>
            )}
            {scraperStatus.items_total > 0 && (
              <span className="text-dark-500 font-mono">{scraperStatus.items_total} items</span>
            )}
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="card animate-slide-up">
        <div className="flex items-center gap-2 mb-5">
          <SlidersHorizontal size={16} className="text-primary-400" />
          <h3 className="font-medium text-sm">Filters</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-8 gap-4">
          <div>
            <label className="block text-[10px] text-dark-500 font-medium uppercase tracking-wider mb-1.5">Search</label>
            <div className="relative">
              <Search size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-dark-500" />
              <input
                type="text"
                value={filters.search}
                onChange={(e) => setFilter("search", e.target.value)}
                placeholder="Item name..."
                className="input w-full pl-10 text-sm"
              />
            </div>
          </div>

          <div>
            <label className="block text-[10px] text-dark-500 font-medium uppercase tracking-wider mb-1.5">
              Min Profit: <span className="text-primary-400">{filters.minProfitPct}%</span>
            </label>
            <input
              type="range"
              min={0}
              max={200}
              value={filters.minProfitPct}
              onChange={(e) => setFilter("minProfitPct", Number(e.target.value))}
              className="w-full accent-primary-500 mt-2"
            />
          </div>

          <div>
            <label className="block text-[10px] text-dark-500 font-medium uppercase tracking-wider mb-1.5">Game</label>
            <select value={filters.game} onChange={(e) => setFilter("game", e.target.value)} className="input w-full text-sm">
              <option value="">All Games</option>
              <option value="cs2">CS2</option>
              <option value="dota2">Dota 2</option>
              <option value="tf2">TF2</option>
              <option value="rust">Rust</option>
            </select>
          </div>

          <div>
            <label className="block text-[10px] text-dark-500 font-medium uppercase tracking-wider mb-1.5">Item Type</label>
            <select value={filters.itemType} onChange={(e) => setFilter("itemType", e.target.value)} className="input w-full text-sm">
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
            <label className="block text-[10px] text-emerald-400 font-medium uppercase tracking-wider mb-1.5">Buy From</label>
            <select value={filters.buyMarketplaceSlug} onChange={(e) => setFilter("buyMarketplaceSlug", e.target.value)} className="input w-full text-sm border-emerald-500/20">
              <option value="">All Marketplaces</option>
              {marketplaces?.map((m) => (
                <option key={m.slug} value={m.slug}>{m.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[10px] text-amber-400 font-medium uppercase tracking-wider mb-1.5">Sell On</label>
            <select value={filters.sellMarketplaceSlug} onChange={(e) => setFilter("sellMarketplaceSlug", e.target.value)} className="input w-full text-sm border-amber-500/20">
              <option value="">All Marketplaces</option>
              {marketplaces?.map((m) => (
                <option key={m.slug} value={m.slug}>{m.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[10px] text-dark-500 font-medium uppercase tracking-wider mb-1.5">Sort By</label>
            <select value={filters.sortBy} onChange={(e) => setFilter("sortBy", e.target.value)} className="input w-full text-sm">
              <option value="profit_pct">Profit %</option>
              <option value="profit_usd">Profit $</option>
              <option value="buy_price">Buy Price</option>
              <option value="sell_price">Sell Price</option>
              <option value="name">Name</option>
            </select>
          </div>

          <div>
            <label className="block text-[10px] text-dark-500 font-medium uppercase tracking-wider mb-1.5">Order</label>
            <select value={filters.sortOrder} onChange={(e) => setFilter("sortOrder", e.target.value)} className="input w-full text-sm">
              <option value="desc">Highest first</option>
              <option value="asc">Lowest first</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="card overflow-x-auto p-0 animate-slide-up" style={{ animationDelay: "100ms" }}>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-dark-700/50">
              <th className="text-left px-5 py-4 text-[10px] text-dark-500 font-semibold uppercase tracking-wider">Item</th>
              <th className="text-right px-4 py-4 text-[10px] text-dark-500 font-semibold uppercase tracking-wider">Buy Price</th>
              <th className="text-left px-4 py-4 text-[10px] text-emerald-400 font-semibold uppercase tracking-wider">Buy From</th>
              <th className="text-center px-2 py-4"></th>
              <th className="text-right px-4 py-4 text-[10px] text-dark-500 font-semibold uppercase tracking-wider">Sell Price (net)</th>
              <th className="text-left px-4 py-4 text-[10px] text-amber-400 font-semibold uppercase tracking-wider">Sell On</th>
              <th className="text-right px-4 py-4 text-[10px] text-dark-500 font-semibold uppercase tracking-wider">Profit</th>
              <th className="text-center px-4 py-4 text-[10px] text-dark-500 font-semibold uppercase tracking-wider">Links</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={8} className="text-center py-16">
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-8 h-8 border-2 border-primary-500/30 border-t-primary-500 rounded-full animate-spin" />
                    <span className="text-dark-400 text-sm">Scanning markets...</span>
                  </div>
                </td>
              </tr>
            ) : !data?.items.length ? (
              <tr>
                <td colSpan={8} className="text-center py-16 text-dark-400">
                  No opportunities found. Adjust your filters.
                </td>
              </tr>
            ) : (
              data.items.map((opp, i) => (
                <tr
                  key={opp.id}
                  className={clsx(
                    "border-b border-dark-700/20 table-row-hover animate-fade-in",
                    opp.profit_pct >= 50 && "bg-amber-500/[0.03]"
                  )}
                  style={{ animationDelay: `${i * 20}ms` }}
                >
                  <td className="px-5 py-3.5">
                    <div className="flex items-center gap-3">
                      {opp.icon_url && (
                        <img
                          src={opp.icon_url}
                          alt=""
                          className="w-9 h-9 rounded-lg object-contain bg-dark-700/50 p-1"
                        />
                      )}
                      <div className="flex flex-col">
                        <span className="font-medium truncate max-w-[220px] text-dark-100" title={opp.market_hash_name}>
                          {opp.market_hash_name}
                        </span>
                        <span className="text-[10px] font-semibold text-dark-500 uppercase tracking-wider">
                          {opp.game}
                        </span>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3.5 text-right font-mono text-dark-200">
                    {formatUSD(opp.buy_price_usd)}
                  </td>
                  <td className="px-4 py-3.5">
                    <span className="text-emerald-400 text-sm font-medium">{opp.buy_marketplace_name}</span>
                  </td>
                  <td className="px-2 py-3.5 text-center">
                    <ArrowRight size={14} className="text-dark-600" />
                  </td>
                  <td className="px-4 py-3.5 text-right font-mono text-dark-300">
                    <div className="flex flex-col items-end">
                      <span>{formatUSD(opp.sell_price_after_fee)}</span>
                      <span className="text-[10px] text-dark-500">-{opp.sell_marketplace_fee_pct}% fee</span>
                    </div>
                  </td>
                  <td className="px-4 py-3.5">
                    <span className="text-amber-400 text-sm font-medium">{opp.sell_marketplace_name}</span>
                  </td>
                  <td className="px-4 py-3.5 text-right">
                    <div className="flex flex-col items-end gap-0.5">
                      <span className={clsx(opp.profit_pct >= 50 ? "badge-high-profit" : "badge-profit")}>
                        +{opp.profit_pct.toFixed(1)}%
                      </span>
                      <span className="text-[10px] text-dark-400 font-mono">+{formatUSD(opp.profit_usd)}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3.5 text-center">
                    <div className="flex items-center justify-center gap-1">
                      <a
                        href={opp.buy_marketplace_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        title={`Buy on ${opp.buy_marketplace_name}`}
                        className="inline-flex p-1.5 rounded-lg text-emerald-400/60 hover:text-emerald-400 hover:bg-emerald-500/10 transition-all"
                      >
                        <ExternalLink size={13} />
                      </a>
                      <a
                        href={opp.sell_marketplace_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        title={`Sell on ${opp.sell_marketplace_name}`}
                        className="inline-flex p-1.5 rounded-lg text-amber-400/60 hover:text-amber-400 hover:bg-amber-500/10 transition-all"
                      >
                        <ExternalLink size={13} />
                      </a>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-center gap-3">
          <button
            onClick={() => setFilter("page", Math.max(1, filters.page - 1))}
            disabled={filters.page <= 1}
            className="btn-secondary text-sm disabled:opacity-30 flex items-center gap-1"
          >
            <ChevronLeft size={16} />
            Previous
          </button>
          <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-dark-800/40 border border-dark-700/30">
            <span className="text-sm font-mono text-primary-400">{filters.page}</span>
            <span className="text-dark-500">/</span>
            <span className="text-sm font-mono text-dark-400">{data.total_pages}</span>
          </div>
          <button
            onClick={() => setFilter("page", Math.min(data.total_pages, filters.page + 1))}
            disabled={filters.page >= data.total_pages}
            className="btn-secondary text-sm disabled:opacity-30 flex items-center gap-1"
          >
            Next
            <ChevronRight size={16} />
          </button>
        </div>
      )}
    </div>
  );
}
