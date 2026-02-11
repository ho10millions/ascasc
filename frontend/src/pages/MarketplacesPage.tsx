import { useQuery } from "@tanstack/react-query";
import { getMarketplaces } from "../api/admin";
import { Globe, Clock, Store, Zap } from "lucide-react";
import clsx from "clsx";

export default function MarketplacesPage() {
  const { data: marketplaces, isLoading } = useQuery({
    queryKey: ["marketplaces"],
    queryFn: getMarketplaces,
  });

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 animate-fade-in">
        <div className="w-10 h-10 border-2 border-primary-500/30 border-t-primary-500 rounded-full animate-spin" />
        <span className="text-dark-400 text-sm mt-4">Loading marketplaces...</span>
      </div>
    );
  }

  const activeCount = marketplaces?.filter((m) => m.is_enabled).length ?? 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between animate-fade-in">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-primary-500/10">
            <Store size={22} className="text-primary-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Marketplaces</h1>
            <p className="text-dark-400 text-sm mt-0.5">
              <span className="text-primary-400 font-semibold">{activeCount}</span> of{" "}
              {marketplaces?.length ?? 0} marketplaces active
            </p>
          </div>
        </div>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {marketplaces
          ?.filter((m) => m.slug !== "steam")
          .map((m, i) => (
            <div
              key={m.id}
              className="card group hover:border-primary-500/20 transition-all duration-300 animate-slide-up"
              style={{ animationDelay: `${i * 50}ms` }}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-dark-100 group-hover:text-primary-400 transition-colors">
                  {m.name}
                </h3>
                <div className="flex items-center gap-2">
                  <span
                    className={clsx(
                      "w-2.5 h-2.5 rounded-full",
                      m.is_enabled ? "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.4)]" : "bg-red-500/70"
                    )}
                  />
                  <span className={clsx(
                    "text-[10px] font-semibold uppercase tracking-wider",
                    m.is_enabled ? "text-emerald-400" : "text-red-400"
                  )}>
                    {m.is_enabled ? "Online" : "Offline"}
                  </span>
                </div>
              </div>

              <div className="space-y-3 text-sm">
                <div className="flex items-center gap-2.5 text-dark-400">
                  <Globe size={14} className="text-dark-500 flex-shrink-0" />
                  <a
                    href={m.base_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary-400/70 hover:text-primary-300 truncate transition-colors text-xs"
                  >
                    {m.base_url}
                  </a>
                </div>
                <div className="flex items-center gap-2.5 text-dark-400">
                  <Clock size={14} className="text-dark-500 flex-shrink-0" />
                  <span className="text-xs">
                    {m.last_scraped_at
                      ? new Date(m.last_scraped_at).toLocaleString()
                      : "Never scraped"}
                  </span>
                </div>
                <div className="flex items-center gap-2.5">
                  <Zap size={14} className="text-dark-500 flex-shrink-0" />
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-semibold bg-dark-700/50 px-2 py-0.5 rounded-md uppercase tracking-wider text-dark-300 border border-dark-700/30">
                      {m.scraper_type}
                    </span>
                    <span className="text-[10px] text-dark-500 font-mono">
                      every {m.scrape_interval_minutes}m
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
      </div>
    </div>
  );
}
