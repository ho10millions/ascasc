import { useAuthStore } from "../../stores/authStore";
import { LogOut, User, Zap } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function Navbar() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <header className="h-16 bg-dark-900/40 backdrop-blur-xl border-b border-dark-700/30 flex items-center justify-between px-8 sticky top-0 z-20">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-primary-500/5 border border-primary-500/10">
          <Zap size={14} className="text-primary-400" />
          <span className="text-xs font-medium text-primary-400">Live</span>
          <span className="dot-online animate-pulse" />
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-3 px-4 py-2 rounded-xl bg-dark-800/40 border border-dark-700/30">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-accent-purple flex items-center justify-center">
            <User size={14} className="text-white" />
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-medium text-dark-100">{user?.username}</span>
            {user?.is_admin && (
              <span className="text-[10px] font-semibold text-amber-400 uppercase tracking-wider">
                Admin
              </span>
            )}
          </div>
        </div>

        <button
          onClick={handleLogout}
          className="p-2.5 rounded-xl text-dark-400 hover:text-red-400 hover:bg-red-500/10 transition-all duration-200"
          title="Logout"
        >
          <LogOut size={18} />
        </button>
      </div>
    </header>
  );
}
