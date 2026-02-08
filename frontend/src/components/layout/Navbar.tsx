import { useAuthStore } from "../../stores/authStore";
import { LogOut, User } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function Navbar() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <header className="h-16 bg-dark-900 border-b border-dark-700 flex items-center justify-between px-6">
      <div>
        <h2 className="text-lg font-semibold text-dark-100">Scrooge's Aggregator</h2>
      </div>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-dark-300">
          <User size={18} />
          <span className="text-sm">{user?.username}</span>
          {user?.is_admin && (
            <span className="text-xs bg-yellow-900/50 text-yellow-400 px-2 py-0.5 rounded-full">
              Admin
            </span>
          )}
        </div>
        <button
          onClick={handleLogout}
          className="text-dark-400 hover:text-red-400 transition-colors"
          title="Logout"
        >
          <LogOut size={18} />
        </button>
      </div>
    </header>
  );
}
