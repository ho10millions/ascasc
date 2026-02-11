import { NavLink } from "react-router-dom";
import { useAuthStore } from "../../stores/authStore";
import MammoniaLogo from "../MammoniaLogo";
import {
  LayoutDashboard,
  TrendingUp,
  Store,
  Shield,
  KeyRound,
  Users,
  Sparkles,
} from "lucide-react";
import clsx from "clsx";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/arbitrage", label: "Arbitrage", icon: TrendingUp },
  { to: "/marketplaces", label: "Marketplaces", icon: Store },
];

const adminItems = [
  { to: "/admin", label: "Admin Panel", icon: Shield },
  { to: "/admin/invite-codes", label: "Invite Codes", icon: KeyRound },
  { to: "/admin/users", label: "Users", icon: Users },
];

export default function Sidebar() {
  const user = useAuthStore((s) => s.user);

  return (
    <aside className="w-72 bg-dark-900/60 backdrop-blur-xl border-r border-dark-700/50 fixed h-full flex flex-col z-30">
      {/* Brand */}
      <div className="p-6 border-b border-dark-700/30">
        <div className="flex items-center gap-3">
          <div className="animate-float">
            <MammoniaLogo size={42} />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-gradient">Mammonia</h1>
            <p className="text-[10px] text-dark-400 font-medium uppercase tracking-[0.2em]">
              Gaming Arbitrage
            </p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        <p className="px-3 mb-3 text-[10px] font-semibold text-dark-500 uppercase tracking-[0.15em]">
          Main
        </p>
        {navItems.map((item, i) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              clsx(
                "group flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200",
                "animate-slide-in-left",
                isActive
                  ? "bg-primary-500/10 text-primary-400 border border-primary-500/20 glow-cyan-sm"
                  : "text-dark-300 hover:bg-dark-800/50 hover:text-dark-100 border border-transparent"
              )
            }
            style={{ animationDelay: `${i * 50}ms` }}
          >
            <item.icon size={18} className="group-hover:scale-110 transition-transform duration-200" />
            {item.label}
          </NavLink>
        ))}

        {user?.is_admin && (
          <>
            <div className="pt-6 pb-2">
              <p className="px-3 text-[10px] font-semibold text-dark-500 uppercase tracking-[0.15em]">
                Admin
              </p>
            </div>
            {adminItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end
                className={({ isActive }) =>
                  clsx(
                    "group flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200",
                    isActive
                      ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                      : "text-dark-300 hover:bg-dark-800/50 hover:text-dark-100 border border-transparent"
                  )
                }
              >
                <item.icon size={18} className="group-hover:scale-110 transition-transform duration-200" />
                {item.label}
              </NavLink>
            ))}
          </>
        )}
      </nav>

      {/* Footer with hidden button */}
      <div className="p-4 border-t border-dark-700/30">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-dark-500">
            <Sparkles size={12} />
            <span className="text-[10px] font-mono">v2.0.0</span>
          </div>
          {/* Hidden button — triple click to activate */}
          <button
            className="w-6 h-6 rounded opacity-0 hover:opacity-20 transition-opacity duration-500 cursor-default"
            onClick={(e) => {
              if (e.detail === 3) {
                window.open("/secret", "_self");
              }
            }}
            aria-hidden="true"
          />
        </div>
      </div>
    </aside>
  );
}
