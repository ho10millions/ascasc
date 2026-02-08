import { useQuery } from "@tanstack/react-query";
import { getMarketplaces } from "../api/admin";
import { Globe, Clock } from "lucide-react";

export default function MarketplacesPage() {
  const { data: marketplaces, isLoading } = useQuery({
    queryKey: ["marketplaces"],
    queryFn: getMarketplaces,
  });

  if (isLoading) {
    return <div className="text-center py-12 text-dark-400">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Marketplaces</h1>
        <p className="text-dark-400 mt-1">
          {marketplaces?.filter((m) => m.is_enabled).length ?? 0} of{" "}
          {marketplaces?.length ?? 0} marketplaces active
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {marketplaces
          ?.filter((m) => m.slug !== "steam")
          .map((m) => (
            <div key={m.id} className="card flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold">{m.name}</h3>
                <span
                  className={`w-3 h-3 rounded-full ${
                    m.is_enabled ? "bg-green-500" : "bg-red-500"
                  }`}
                />
              </div>
              <div className="space-y-2 text-sm text-dark-400">
                <div className="flex items-center gap-2">
                  <Globe size={14} />
                  <a
                    href={m.base_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary-400 hover:text-primary-300 truncate"
                  >
                    {m.base_url}
                  </a>
                </div>
                <div className="flex items-center gap-2">
                  <Clock size={14} />
                  <span>
                    {m.last_scraped_at
                      ? `Last scraped: ${new Date(m.last_scraped_at).toLocaleString()}`
                      : "Never scraped"}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs bg-dark-700 px-2 py-0.5 rounded">
                    {m.scraper_type}
                  </span>
                  <span className="text-xs text-dark-500">
                    every {m.scrape_interval_minutes} min
                  </span>
                </div>
              </div>
            </div>
          ))}
      </div>
    </div>
  );
}
