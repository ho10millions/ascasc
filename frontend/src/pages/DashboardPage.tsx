import { useQuery } from "@tanstack/react-query";
import { getArbitrageStats } from "../api/arbitrage";
import { getMarketplaces } from "../api/admin";
import { TrendingUp, DollarSign, Package, Zap, Activity, ArrowUpRight } from "lucide-react";
import { useNavigate } from "react-router-dom";

function StatCard({
  label,
  value,
  icon: Icon,
  gradient,
  delay = 0,
}: {
  label: string;
  value: string | number;
  icon: any;
  gradient: string;
  delay?: number;
}) {
  return (
    <div
      className="card-hover group animate-slide-up"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-start justify-between mb-4">
        <div className={`p-3 rounded-xl ${gradient} transition-transform duration-300 group-hover:scale-110`}>
          <Icon size={20} />
        </div>
        <ArrowUpRight size={16} className="text-dark-500 group-hover:text-primary-400 transition-colors" />
      </div>
      <p className="stat-value text-dark-100">{value}</p>
      <p className="text-sm text-dark-400 mt-1">{label}</p>
    </div>
  );
}

export default function DashboardPage() {
  const navigate = useNavigate();
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
    <div className="space-y-8">
      {/* Header */}
      <div className="animate-fade-in">
        <h1 className="text-3xl font-bold tracking-tight">
          Welcome to <span className="text-gradient">Mammonia</span>
        </h1>
        <p className="text-dark-400 mt-2">Real-time arbitrage monitoring across gaming marketplaces</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard
          label="Active Opportunities"
          value={stats?.active_opportunities ?? 0}
          icon={TrendingUp}
          gradient="bg-primary-500/10 text-primary-400"
          delay={0}
        />
        <StatCard
          label="High Value (>50%)"
          value={stats?.high_value_opportunities ?? 0}
          icon={Zap}
          gradient="bg-amber-500/10 text-amber-400"
          delay={100}
        />
        <StatCard
          label="Max Profit"
          value={stats?.max_profit_pct ? `${stats.max_profit_pct.toFixed(1)}%` : "N/A"}
          icon={DollarSign}
          gradient="bg-emerald-500/10 text-emerald-400"
          delay={200}
        />
        <StatCard
          label="Items Tracked"
          value={stats?.total_items_tracked ?? 0}
          icon={Package}
          gradient="bg-blue-500/10 text-blue-400"
          delay={300}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* System Status */}
        <div className="card animate-slide-up" style={{ animationDelay: "200ms" }}>
          <div className="flex items-center gap-2 mb-5">
            <Activity size={18} className="text-primary-400" />
            <h2 className="text-lg font-semibold">System Status</h2>
          </div>
          <div className="space-y-4">
            {[
              { label: "Marketplaces Enabled", value: `${enabledCount} / ${marketplaces?.length ?? 0}`, color: "text-dark-100" },
              { label: "Recently Scraped (1h)", value: recentlyScraped, color: "text-dark-100" },
              { label: "Avg Profit", value: stats?.avg_profit_pct ? `${stats.avg_profit_pct.toFixed(1)}%` : "N/A", color: "text-profit" },
            ].map((item, i) => (
              <div key={i} className="flex justify-between items-center py-2 border-b border-dark-700/30 last:border-0">
                <span className="text-sm text-dark-400">{item.label}</span>
                <span className={`font-semibold font-mono ${item.color}`}>{item.value}</span>
              </div>
            ))}
          </div>

          <button
            onClick={() => navigate("/arbitrage")}
            className="btn-primary w-full mt-5 flex items-center justify-center gap-2 group"
          >
            View Arbitrage
            <ArrowUpRight size={16} className="group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
          </button>
        </div>

        {/* Marketplace Status */}
        <div className="card animate-slide-up" style={{ animationDelay: "300ms" }}>
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              <Package size={18} className="text-primary-400" />
              <h2 className="text-lg font-semibold">Marketplaces</h2>
            </div>
            <button
              onClick={() => navigate("/marketplaces")}
              className="text-xs text-dark-400 hover:text-primary-400 transition-colors"
            >
              View all
            </button>
          </div>
          <div className="space-y-2 max-h-72 overflow-y-auto">
            {marketplaces
              ?.filter((m) => m.slug !== "steam")
              .slice(0, 12)
              .map((m) => (
                <div
                  key={m.id}
                  className="flex justify-between items-center py-2.5 px-3 rounded-xl hover:bg-dark-700/30 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <span className={m.is_enabled ? "dot-online" : "dot-offline"} />
                    <span className="text-sm font-medium text-dark-200">{m.name}</span>
                  </div>
                  <span className="text-xs text-dark-500 font-mono">
                    {m.last_scraped_at
                      ? new Date(m.last_scraped_at).toLocaleTimeString()
                      : "Never"}
                  </span>
                </div>
              ))}
          </div>
        </div>
      </div>
    </div>
  );
}
