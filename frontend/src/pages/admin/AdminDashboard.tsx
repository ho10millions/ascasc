import { useQuery } from "@tanstack/react-query";
import { getScrapeJobs, getMarketplaces } from "../../api/admin";
import { getArbitrageStats } from "../../api/arbitrage";
import { Activity, Database, AlertTriangle, CheckCircle } from "lucide-react";

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

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Admin Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card flex items-center gap-4">
          <div className="p-3 rounded-lg bg-blue-900/50 text-blue-400">
            <Database size={24} />
          </div>
          <div>
            <p className="text-sm text-dark-400">Total Items</p>
            <p className="text-2xl font-bold">{stats?.total_items_tracked ?? 0}</p>
          </div>
        </div>
        <div className="card flex items-center gap-4">
          <div className="p-3 rounded-lg bg-green-900/50 text-green-400">
            <Activity size={24} />
          </div>
          <div>
            <p className="text-sm text-dark-400">Active Marketplaces</p>
            <p className="text-2xl font-bold">
              {marketplaces?.filter((m) => m.is_enabled).length ?? 0}
            </p>
          </div>
        </div>
        <div className="card flex items-center gap-4">
          <div className="p-3 rounded-lg bg-green-900/50 text-green-400">
            <CheckCircle size={24} />
          </div>
          <div>
            <p className="text-sm text-dark-400">Recent Successful</p>
            <p className="text-2xl font-bold">
              {recentJobs.filter((j) => j.status === "completed").length}
            </p>
          </div>
        </div>
        <div className="card flex items-center gap-4">
          <div className="p-3 rounded-lg bg-red-900/50 text-red-400">
            <AlertTriangle size={24} />
          </div>
          <div>
            <p className="text-sm text-dark-400">Recent Failed</p>
            <p className="text-2xl font-bold">{failedJobs.length}</p>
          </div>
        </div>
      </div>

      {/* Recent Scrape Jobs */}
      <div className="card p-0 overflow-x-auto">
        <div className="px-6 py-4 border-b border-dark-700">
          <h2 className="font-semibold">Recent Scrape Jobs</h2>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-dark-700">
              <th className="text-left px-4 py-3 text-dark-400 font-medium">Marketplace</th>
              <th className="text-left px-4 py-3 text-dark-400 font-medium">Status</th>
              <th className="text-right px-4 py-3 text-dark-400 font-medium">Items</th>
              <th className="text-left px-4 py-3 text-dark-400 font-medium">Triggered</th>
              <th className="text-right px-4 py-3 text-dark-400 font-medium">Started</th>
              <th className="text-right px-4 py-3 text-dark-400 font-medium">Finished</th>
            </tr>
          </thead>
          <tbody>
            {recentJobs.map((job) => {
              const mkt = marketplaces?.find((m) => m.id === job.marketplace_id);
              return (
                <tr key={job.id} className="border-b border-dark-800 hover:bg-dark-800/50">
                  <td className="px-4 py-3 font-medium">{mkt?.name ?? `#${job.marketplace_id}`}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full ${
                        job.status === "completed"
                          ? "bg-green-900/50 text-green-400"
                          : job.status === "running"
                          ? "bg-blue-900/50 text-blue-400"
                          : job.status === "failed"
                          ? "bg-red-900/50 text-red-400"
                          : "bg-dark-700 text-dark-400"
                      }`}
                    >
                      {job.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-mono">{job.items_scraped}</td>
                  <td className="px-4 py-3 text-dark-400">{job.triggered_by}</td>
                  <td className="px-4 py-3 text-right text-dark-400 text-xs">
                    {job.started_at ? new Date(job.started_at).toLocaleString() : "—"}
                  </td>
                  <td className="px-4 py-3 text-right text-dark-400 text-xs">
                    {job.finished_at ? new Date(job.finished_at).toLocaleString() : "—"}
                  </td>
                </tr>
              );
            })}
            {recentJobs.length === 0 && (
              <tr>
                <td colSpan={6} className="text-center py-8 text-dark-400">
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
