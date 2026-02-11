import { useQuery } from "@tanstack/react-query";
import { getScrapeJobs, getMarketplaces } from "../../api/admin";
import { getArbitrageStats } from "../../api/arbitrage";
import { Activity, Database, AlertTriangle, CheckCircle, Shield, Terminal } from "lucide-react";
import clsx from "clsx";

export default function AdminDashboard() {
  const { data: stats } = useQuery({
    queryKey: ["arbitrage-stats"],
    queryFn: getArbitrageStats,
  });

  const { data: marketplaces } = useQuery({
    queryKey: ["marketplaces"],
    queryFn: getMarketplaces,
  });

  const { data: jobs } = useQuery({
    queryKey: ["scrape-jobs"],
    queryFn: () => getScrapeJobs(),
    refetchInterval: 30_000,
  });

  const recentJobs = jobs?.slice(0, 20) ?? [];
  const failedJobs = recentJobs.filter((j) => j.status === "failed");

  const statCards = [
    { label: "Total Items", value: stats?.total_items_tracked ?? 0, icon: Database, color: "primary" },
    { label: "Active Marketplaces", value: marketplaces?.filter((m) => m.is_enabled).length ?? 0, icon: Activity, color: "emerald" },
    { label: "Recent Successful", value: recentJobs.filter((j) => j.status === "completed").length, icon: CheckCircle, color: "emerald" },
    { label: "Recent Failed", value: failedJobs.length, icon: AlertTriangle, color: "red" },
  ];

  const colorMap: Record<string, string> = {
    primary: "bg-primary-500/10 text-primary-400 border-primary-500/20",
    emerald: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    red: "bg-red-500/10 text-red-400 border-red-500/20",
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 animate-fade-in">
        <div className="p-2.5 rounded-xl bg-amber-500/10">
          <Shield size={22} className="text-amber-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Admin Dashboard</h1>
          <p className="text-dark-400 text-sm mt-0.5">System overview and scrape jobs</p>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card, i) => (
          <div
            key={card.label}
            className="card group hover:-translate-y-0.5 transition-all duration-300 animate-slide-up"
            style={{ animationDelay: `${i * 50}ms` }}
          >
            <div className="flex items-center gap-4">
              <div className={clsx("p-3 rounded-xl border", colorMap[card.color])}>
                <card.icon size={22} className="group-hover:scale-110 transition-transform duration-300" />
              </div>
              <div>
                <p className="text-[10px] text-dark-500 font-medium uppercase tracking-wider">{card.label}</p>
                <p className="text-2xl font-bold font-mono text-dark-100">{card.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Scrape Jobs */}
      <div className="card overflow-x-auto p-0 animate-slide-up" style={{ animationDelay: "200ms" }}>
        <div className="px-5 py-4 border-b border-dark-700/50 flex items-center gap-2">
          <Terminal size={16} className="text-primary-400" />
          <h2 className="font-medium text-sm">Recent Scrape Jobs</h2>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-dark-700/50">
              <th className="text-left px-5 py-3 text-[10px] text-dark-500 font-semibold uppercase tracking-wider">Marketplace</th>
              <th className="text-left px-4 py-3 text-[10px] text-dark-500 font-semibold uppercase tracking-wider">Status</th>
              <th className="text-right px-4 py-3 text-[10px] text-dark-500 font-semibold uppercase tracking-wider">Items</th>
              <th className="text-left px-4 py-3 text-[10px] text-dark-500 font-semibold uppercase tracking-wider">Triggered</th>
              <th className="text-right px-4 py-3 text-[10px] text-dark-500 font-semibold uppercase tracking-wider">Started</th>
              <th className="text-right px-4 py-3 text-[10px] text-dark-500 font-semibold uppercase tracking-wider">Finished</th>
            </tr>
          </thead>
          <tbody>
            {recentJobs.map((job, i) => {
              const mkt = marketplaces?.find((m) => m.id === job.marketplace_id);
              return (
                <tr
                  key={job.id}
                  className="border-b border-dark-700/20 table-row-hover animate-fade-in"
                  style={{ animationDelay: `${i * 20}ms` }}
                >
                  <td className="px-5 py-3 font-medium text-dark-200">{mkt?.name ?? `#${job.marketplace_id}`}</td>
                  <td className="px-4 py-3">
                    <span
                      className={clsx(
                        "text-[10px] font-semibold px-2.5 py-1 rounded-lg uppercase tracking-wider border",
                        job.status === "completed" && "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
                        job.status === "running" && "bg-primary-500/10 text-primary-400 border-primary-500/20",
                        job.status === "failed" && "bg-red-500/10 text-red-400 border-red-500/20",
                        job.status !== "completed" && job.status !== "running" && job.status !== "failed" && "bg-dark-700/50 text-dark-400 border-dark-700/30"
                      )}
                    >
                      {job.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-dark-300">{job.items_scraped}</td>
                  <td className="px-4 py-3 text-dark-400 text-xs">{job.triggered_by}</td>
                  <td className="px-4 py-3 text-right text-dark-500 text-xs font-mono">
                    {job.started_at ? new Date(job.started_at).toLocaleString() : "—"}
                  </td>
                  <td className="px-4 py-3 text-right text-dark-500 text-xs font-mono">
                    {job.finished_at ? new Date(job.finished_at).toLocaleString() : "—"}
                  </td>
                </tr>
              );
            })}
            {recentJobs.length === 0 && (
              <tr>
                <td colSpan={6} className="text-center py-16 text-dark-400">
                  No scrape jobs yet
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
