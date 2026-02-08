import { NavLink } from "react-router-dom";
import { useAuthStore } from "../../stores/authStore";
import {
  LayoutDashboard,
  TrendingUp,
  Store,
  Shield,
  KeyRound,
  Users,
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
    <aside className="w-64 bg-dark-900 border-r border-dark-700 fixed h-full flex flex-col">
      <div className="p-6 border-b border-dark-700">
        <h1 className="text-xl font-bold text-gold">Scrooge's</h1>
        <p className="text-xs text-dark-400 mt-1">Price Aggregator & Arbitrage Hunter</p>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm transition-colors",
                isActive
                  ? "bg-primary-600/20 text-primary-400"
                  : "text-dark-300 hover:bg-dark-800 hover:text-dark-100"
              )
            }
          >
            <item.icon size={18} />
            {item.label}
          </NavLink>
        ))}

        {user?.is_admin && (
          <>
            <div className="pt-4 pb-2">
              <p className="px-4 text-xs font-semibold text-dark-500 uppercase tracking-wider">
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
                    "flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm transition-colors",
                    isActive
                      ? "bg-yellow-600/20 text-yellow-400"
                      : "text-dark-300 hover:bg-dark-800 hover:text-dark-100"
                  )
                }
              >
                <item.icon size={18} />
                {item.label}
              </NavLink>
            ))}
          </>
        )}
      </nav>

      <div className="p-4 border-t border-dark-700">
        <p className="text-xs text-dark-500 text-center">v1.0.0</p>
      </div>
    </aside>
  );
}
