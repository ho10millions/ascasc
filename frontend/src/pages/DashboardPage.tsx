import { useQuery } from "@tanstack/react-query";
import { getArbitrageStats } from "../api/arbitrage";
import { getMarketplaces } from "../api/admin";
import { TrendingUp, DollarSign, Package, Zap } from "lucide-react";

function StatCard({
  label,
  value,
  icon: Icon,
  color,
}: {
  label: string;
  value: string | number;
  icon: any;
  color: string;
}) {
  return (
    <div className="card flex items-center gap-4">
      <div className={`p-3 rounded-lg ${color}`}>
        <Icon size={24} />
      </div>
      <div>
        <p className="text-sm text-dark-400">{label}</p>
        <p className="text-2xl font-bold">{value}</p>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { data: stats } = useQuery({
    queryKey: ["arbitrage-stats"],
    queryFn: getArbitrageStats,
    refetchInterval: 60_000,
  });

  const { data: marketplaces } = useQuery({
    queryKey: ["marketplaces"],
    queryFn: getMarketplaces,
  });

  const enabledCount = marketplaces?.filter((m) => m.is_enabled).length ?? 0;
  const recentlyScraped = marketplaces?.filter(
    (m) => m.last_scraped_at && new Date(m.last_scraped_at) > new Date(Date.now() - 3600_000)
  ).length ?? 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-dark-400 mt-1">Overview of arbitrage opportunities and system status</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Active Opportunities"
          value={stats?.active_opportunities ?? 0}
          icon={TrendingUp}
          color="bg-primary-900/50 text-primary-400"
        />
        <StatCard
          label="High Value (>50%)"
          value={stats?.high_value_opportunities ?? 0}
          icon={Zap}
          color="bg-yellow-900/50 text-yellow-400"
        />
        <StatCard
          label="Max Profit"
          value={stats?.max_profit_pct ? `${stats.max_profit_pct}%` : "N/A"}
          icon={DollarSign}
          color="bg-green-900/50 text-green-400"
        />
        <StatCard
          label="Items Tracked"
          value={stats?.total_items_tracked ?? 0}
          icon={Package}
          color="bg-blue-900/50 text-blue-400"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">System Status</h2>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-dark-300">Marketplaces Enabled</span>
              <span className="font-medium">{enabledCount} / {marketplaces?.length ?? 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-dark-300">Recently Scraped (1h)</span>
              <span className="font-medium">{recentlyScraped}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-dark-300">Avg Profit</span>
              <span className="font-medium text-profit">
                {stats?.avg_profit_pct ? `${stats.avg_profit_pct}%` : "N/A"}
              </span>
            </div>
          </div>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Marketplace Status</h2>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {marketplaces
              ?.filter((m) => m.slug !== "steam")
              .slice(0, 10)
              .map((m) => (
                <div key={m.id} className="flex justify-between items-center text-sm">
                  <span className="text-dark-300">{m.name}</span>
                  <div className="flex items-center gap-2">
                    <span
                      className={`w-2 h-2 rounded-full ${
                        m.is_enabled ? "bg-green-500" : "bg-red-500"
                      }`}
                    />
                    <span className="text-dark-400 text-xs">
                      {m.last_scraped_at
                        ? new Date(m.last_scraped_at).toLocaleTimeString()
                        : "Never"}
                    </span>
                  </div>
                </div>
              ))}
          </div>
        </div>
      </div>
    </div>
  );
}
