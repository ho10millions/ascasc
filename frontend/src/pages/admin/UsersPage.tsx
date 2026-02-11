import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getUsers, toggleUserActive } from "../../api/admin";
import { useAuthStore } from "../../stores/authStore";
import { Users, ShieldCheck, ShieldOff } from "lucide-react";
import clsx from "clsx";

export default function UsersPage() {
  const queryClient = useQueryClient();
  const currentUser = useAuthStore((s) => s.user);

  const { data: users, isLoading } = useQuery({
    queryKey: ["admin-users"],
    queryFn: getUsers,
  });

  const toggleMutation = useMutation({
    mutationFn: ({ userId, isActive }: { userId: string; isActive: boolean }) =>
      toggleUserActive(userId, isActive),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-users"] }),
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 animate-fade-in">
        <div className="p-2.5 rounded-xl bg-amber-500/10">
          <Users size={22} className="text-amber-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">User Management</h1>
          <p className="text-dark-400 text-sm mt-0.5">
            <span className="text-primary-400 font-semibold">{users?.length ?? 0}</span> registered users
          </p>
        </div>
      </div>

      {/* Table */}
      <div className="card overflow-x-auto p-0 animate-slide-up">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-dark-700/50">
              <th className="text-left px-5 py-4 text-[10px] text-dark-500 font-semibold uppercase tracking-wider">Username</th>
              <th className="text-left px-4 py-4 text-[10px] text-dark-500 font-semibold uppercase tracking-wider">Email</th>
              <th className="text-center px-4 py-4 text-[10px] text-dark-500 font-semibold uppercase tracking-wider">Role</th>
              <th className="text-center px-4 py-4 text-[10px] text-dark-500 font-semibold uppercase tracking-wider">Status</th>
              <th className="text-right px-4 py-4 text-[10px] text-dark-500 font-semibold uppercase tracking-wider">Registered</th>
              <th className="text-center px-4 py-4 text-[10px] text-dark-500 font-semibold uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={6} className="text-center py-16">
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-8 h-8 border-2 border-primary-500/30 border-t-primary-500 rounded-full animate-spin" />
                    <span className="text-dark-400 text-sm">Loading users...</span>
                  </div>
                </td>
              </tr>
            ) : (
              users?.map((user, i) => (
                <tr
                  key={user.id}
                  className="border-b border-dark-700/20 table-row-hover animate-fade-in"
                  style={{ animationDelay: `${i * 20}ms` }}
                >
                  <td className="px-5 py-3.5">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500/20 to-accent-purple/20 flex items-center justify-center border border-dark-700/30">
                        <span className="text-xs font-bold text-primary-400">{user.username[0]?.toUpperCase()}</span>
                      </div>
                      <span className="font-medium text-dark-200">{user.username}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3.5 text-dark-400 text-xs">{user.email}</td>
                  <td className="px-4 py-3.5 text-center">
                    {user.is_admin ? (
                      <span className="text-[10px] font-semibold text-amber-400 bg-amber-500/10 px-2.5 py-1 rounded-lg border border-amber-500/20 uppercase tracking-wider">
                        Admin
                      </span>
                    ) : (
                      <span className="text-[10px] font-semibold text-dark-400 bg-dark-700/50 px-2.5 py-1 rounded-lg border border-dark-700/30 uppercase tracking-wider">
                        User
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3.5 text-center">
                    <span
                      className={clsx(
                        "text-[10px] font-semibold px-2.5 py-1 rounded-lg uppercase tracking-wider border",
                        user.is_active
                          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                          : "bg-red-500/10 text-red-400 border-red-500/20"
                      )}
                    >
                      {user.is_active ? "Active" : "Disabled"}
                    </span>
                  </td>
                  <td className="px-4 py-3.5 text-right text-dark-500 text-xs font-mono">
                    {new Date(user.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3.5 text-center">
                    {user.id !== currentUser?.id && (
                      <button
                        onClick={() =>
                          toggleMutation.mutate({
                            userId: user.id,
                            isActive: !user.is_active,
                          })
                        }
                        className={clsx(
                          "inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg transition-all",
                          user.is_active
                            ? "text-red-400 bg-red-500/10 border border-red-500/20 hover:bg-red-500/20"
                            : "text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 hover:bg-emerald-500/20"
                        )}
                      >
                        {user.is_active ? (
                          <><ShieldOff size={12} /> Disable</>
                        ) : (
                          <><ShieldCheck size={12} /> Enable</>
                        )}
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
