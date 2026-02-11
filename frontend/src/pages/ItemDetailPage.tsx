import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getItem, getItemPrices } from "../api/items";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { ArrowLeft, ExternalLink, Tag, Gamepad2 } from "lucide-react";
import clsx from "clsx";

function formatUSD(value: number): string {
  return `$${value.toFixed(2)}`;
}

export default function ItemDetailPage() {
  const { itemId } = useParams<{ itemId: string }>();
  const navigate = useNavigate();

  const { data: item, isLoading: itemLoading } = useQuery({
    queryKey: ["item", itemId],
    queryFn: () => getItem(itemId!),
    enabled: !!itemId,
  });

  const { data: priceComparison, isLoading: pricesLoading } = useQuery({
    queryKey: ["item-prices", itemId],
    queryFn: () => getItemPrices(itemId!),
    enabled: !!itemId,
  });

  if (itemLoading || pricesLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 animate-fade-in">
        <div className="w-10 h-10 border-2 border-primary-500/30 border-t-primary-500 rounded-full animate-spin" />
        <span className="text-dark-400 text-sm mt-4">Loading item data...</span>
      </div>
    );
  }

  if (!item) {
    return (
      <div className="flex flex-col items-center justify-center py-24 animate-fade-in">
        <span className="text-dark-400 text-lg">Item not found</span>
        <button onClick={() => navigate(-1)} className="btn-secondary mt-4 text-sm">
          Go Back
        </button>
      </div>
    );
  }

  const chartData = priceComparison?.prices.map((p) => ({
    name: p.marketplace_name,
    price: p.price_usd,
  })) ?? [];

  const minPrice = chartData.length > 0 ? Math.min(...chartData.map((d) => d.price)) : 0;

  return (
    <div className="space-y-6">
      {/* Back button */}
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-2 text-dark-400 hover:text-primary-400 transition-colors text-sm group"
      >
        <ArrowLeft size={16} className="group-hover:-translate-x-1 transition-transform" />
        Back
      </button>

      {/* Item Header */}
      <div className="card flex items-center gap-6 animate-fade-in">
        {item.icon_url && (
          <div className="w-24 h-24 rounded-2xl bg-dark-700/50 p-3 border border-dark-700/30 flex-shrink-0">
            <img
              src={item.icon_url}
              alt={item.market_hash_name}
              className="w-full h-full object-contain"
            />
          </div>
        )}
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-dark-100">{item.market_hash_name}</h1>
          <div className="flex items-center gap-3 mt-3">
            <span className="flex items-center gap-1.5 text-[10px] font-semibold bg-dark-700/50 px-2.5 py-1 rounded-lg uppercase tracking-wider text-dark-300 border border-dark-700/30">
              <Gamepad2 size={12} />
              {item.game}
            </span>
            {item.item_type && (
              <span className="flex items-center gap-1.5 text-[10px] font-semibold bg-primary-500/10 px-2.5 py-1 rounded-lg text-primary-400 border border-primary-500/20">
                <Tag size={12} />
                {item.item_type}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Steam Price */}
      {priceComparison?.steam_price && (
        <div className="card animate-slide-up">
          <h2 className="text-sm font-semibold mb-4 flex items-center gap-2 text-dark-300 uppercase tracking-wider">
            Steam Market Price
          </h2>
          <div className="grid grid-cols-2 gap-6">
            <div className="p-4 rounded-xl bg-dark-800/40 border border-dark-700/30">
              <p className="text-[10px] text-dark-500 font-medium uppercase tracking-wider mb-1">Listing Price</p>
              <p className="text-2xl font-bold font-mono text-dark-100">{formatUSD(priceComparison.steam_price)}</p>
            </div>
            <div className="p-4 rounded-xl bg-primary-500/5 border border-primary-500/20">
              <p className="text-[10px] text-dark-500 font-medium uppercase tracking-wider mb-1">After Fee (87%)</p>
              <p className="text-2xl font-bold font-mono text-primary-400">
                {formatUSD(priceComparison.steam_price_after_fee!)}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Price Comparison Chart */}
      {chartData.length > 0 && (
        <div className="card animate-slide-up" style={{ animationDelay: "50ms" }}>
          <h2 className="text-sm font-semibold mb-5 text-dark-300 uppercase tracking-wider">Price Comparison</h2>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} layout="vertical" margin={{ left: 100 }}>
                <XAxis type="number" tickFormatter={(v) => `$${v}`} stroke="#334155" fontSize={11} />
                <YAxis type="category" dataKey="name" stroke="#334155" width={90} tick={{ fontSize: 11, fill: "#94a3b8" }} />
                <Tooltip
                  formatter={(value: number) => formatUSD(value)}
                  contentStyle={{
                    background: "rgba(10, 18, 30, 0.95)",
                    border: "1px solid rgba(6, 182, 212, 0.2)",
                    borderRadius: 12,
                    backdropFilter: "blur(8px)",
                    boxShadow: "0 8px 32px rgba(0,0,0,0.3)",
                  }}
                  labelStyle={{ color: "#e2e8f0", fontWeight: 600 }}
                  itemStyle={{ color: "#06b6d4" }}
                />
                <Bar dataKey="price" radius={[0, 6, 6, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell
                      key={index}
                      fill={entry.price === minPrice ? "#06b6d4" : "#1e3a5f"}
                      stroke={entry.price === minPrice ? "#22d3ee" : "transparent"}
                      strokeWidth={1}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Price Table */}
      <div className="card overflow-x-auto p-0 animate-slide-up" style={{ animationDelay: "100ms" }}>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-dark-700/50">
              <th className="text-left px-5 py-4 text-[10px] text-dark-500 font-semibold uppercase tracking-wider">Marketplace</th>
              <th className="text-right px-4 py-4 text-[10px] text-dark-500 font-semibold uppercase tracking-wider">Price</th>
              <th className="text-right px-4 py-4 text-[10px] text-dark-500 font-semibold uppercase tracking-wider">Listings</th>
              <th className="text-right px-4 py-4 text-[10px] text-dark-500 font-semibold uppercase tracking-wider">Updated</th>
              <th className="text-right px-4 py-4 text-[10px] text-dark-500 font-semibold uppercase tracking-wider">Profit vs Steam</th>
            </tr>
          </thead>
          <tbody>
            {priceComparison?.prices.map((p, i) => {
              const profitPct =
                priceComparison.steam_price_after_fee && p.price_usd > 0
                  ? ((priceComparison.steam_price_after_fee / p.price_usd - 1) * 100)
                  : null;
              return (
                <tr
                  key={i}
                  className={clsx(
                    "border-b border-dark-700/20 table-row-hover animate-fade-in",
                    p.price_usd === minPrice && "bg-primary-500/[0.03]"
                  )}
                  style={{ animationDelay: `${i * 30}ms` }}
                >
                  <td className="px-5 py-3.5 font-medium">
                    <a
                      href={p.marketplace_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary-400 hover:text-primary-300 transition-colors inline-flex items-center gap-2"
                    >
                      {p.marketplace_name}
                      <ExternalLink size={12} className="opacity-50" />
                    </a>
                  </td>
                  <td className="px-4 py-3.5 text-right font-mono text-dark-200">{formatUSD(p.price_usd)}</td>
                  <td className="px-4 py-3.5 text-right text-dark-400">
                    {p.listing_count ?? "—"}
                  </td>
                  <td className="px-4 py-3.5 text-right text-dark-500 text-xs font-mono">
                    {new Date(p.scraped_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3.5 text-right">
                    {profitPct !== null ? (
                      <span className={clsx(
                        profitPct >= 50 ? "badge-high-profit" : profitPct > 0 ? "badge-profit" : "text-red-400 text-sm font-medium"
                      )}>
                        {profitPct > 0 ? "+" : ""}{profitPct.toFixed(1)}%
                      </span>
                    ) : (
                      <span className="text-dark-500">—</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
