import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getItem, getItemPrices } from "../api/items";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

function formatUSD(value: number): string {
  return `$${value.toFixed(2)}`;
}

export default function ItemDetailPage() {
  const { itemId } = useParams<{ itemId: string }>();

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
    return <div className="text-center py-12 text-dark-400">Loading...</div>;
  }

  if (!item) {
    return <div className="text-center py-12 text-dark-400">Item not found</div>;
  }

  const chartData = priceComparison?.prices.map((p) => ({
    name: p.marketplace_name,
    price: p.price_usd,
  })) ?? [];

  const minPrice = chartData.length > 0 ? Math.min(...chartData.map((d) => d.price)) : 0;

  return (
    <div className="space-y-6">
      <div className="card flex items-center gap-6">
        {item.icon_url && (
          <img
            src={item.icon_url}
            alt={item.market_hash_name}
            className="w-24 h-24 rounded-lg object-contain bg-dark-800 p-2"
          />
        )}
        <div>
          <h1 className="text-2xl font-bold">{item.market_hash_name}</h1>
          <div className="flex items-center gap-3 mt-2">
            <span className="text-xs bg-dark-700 px-2 py-1 rounded uppercase">{item.game}</span>
            {item.item_type && (
              <span className="text-xs bg-dark-700 px-2 py-1 rounded">{item.item_type}</span>
            )}
          </div>
        </div>
      </div>

      {/* Steam Price */}
      {priceComparison?.steam_price && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-3">Steam Market Price</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-dark-400">Listing Price</p>
              <p className="text-xl font-bold">{formatUSD(priceComparison.steam_price)}</p>
            </div>
            <div>
              <p className="text-sm text-dark-400">After Fee (87%)</p>
              <p className="text-xl font-bold text-profit">
                {formatUSD(priceComparison.steam_price_after_fee!)}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Price Comparison Chart */}
      {chartData.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Price Comparison</h2>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} layout="vertical" margin={{ left: 100 }}>
                <XAxis type="number" tickFormatter={(v) => `$${v}`} stroke="#64748b" />
                <YAxis type="category" dataKey="name" stroke="#64748b" width={90} tick={{ fontSize: 12 }} />
                <Tooltip
                  formatter={(value: number) => formatUSD(value)}
                  contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
                  labelStyle={{ color: "#e2e8f0" }}
                />
                <Bar dataKey="price" radius={[0, 4, 4, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell
                      key={index}
                      fill={entry.price === minPrice ? "#22c55e" : "#3b82f6"}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Price Table */}
      <div className="card p-0 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-dark-700">
              <th className="text-left px-4 py-3 text-dark-400 font-medium">Marketplace</th>
              <th className="text-right px-4 py-3 text-dark-400 font-medium">Price</th>
              <th className="text-right px-4 py-3 text-dark-400 font-medium">Listings</th>
              <th className="text-right px-4 py-3 text-dark-400 font-medium">Updated</th>
              <th className="text-right px-4 py-3 text-dark-400 font-medium">Profit vs Steam</th>
            </tr>
          </thead>
          <tbody>
            {priceComparison?.prices.map((p, i) => {
              const profitPct =
                priceComparison.steam_price_after_fee && p.price_usd > 0
                  ? ((priceComparison.steam_price_after_fee / p.price_usd - 1) * 100)
                  : null;
              return (
                <tr key={i} className="border-b border-dark-800 hover:bg-dark-800/50">
                  <td className="px-4 py-3 font-medium">
                    <a
                      href={p.marketplace_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary-400 hover:text-primary-300"
                    >
                      {p.marketplace_name}
                    </a>
                  </td>
                  <td className="px-4 py-3 text-right font-mono">{formatUSD(p.price_usd)}</td>
                  <td className="px-4 py-3 text-right text-dark-400">
                    {p.listing_count ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-right text-dark-400 text-xs">
                    {new Date(p.scraped_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {profitPct !== null ? (
                      <span className={profitPct >= 50 ? "badge-high-profit" : profitPct > 0 ? "badge-profit" : "text-red-400"}>
                        {profitPct > 0 ? "+" : ""}{profitPct.toFixed(1)}%
                      </span>
                    ) : (
                      "—"
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
