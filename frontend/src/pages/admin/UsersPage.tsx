import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getUsers, toggleUserActive } from "../../api/admin";
import { useAuthStore } from "../../stores/authStore";

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
      <div>
        <h1 className="text-2xl font-bold">User Management</h1>
        <p className="text-dark-400 mt-1">{users?.length ?? 0} registered users</p>
      </div>

      <div className="card p-0 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-dark-700">
              <th className="text-left px-4 py-3 text-dark-400 font-medium">Username</th>
              <th className="text-left px-4 py-3 text-dark-400 font-medium">Email</th>
              <th className="text-center px-4 py-3 text-dark-400 font-medium">Role</th>
              <th className="text-center px-4 py-3 text-dark-400 font-medium">Status</th>
              <th className="text-right px-4 py-3 text-dark-400 font-medium">Registered</th>
              <th className="text-center px-4 py-3 text-dark-400 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={6} className="text-center py-8 text-dark-400">Loading...</td>
              </tr>
            ) : (
              users?.map((user) => (
                <tr key={user.id} className="border-b border-dark-800 hover:bg-dark-800/50">
                  <td className="px-4 py-3 font-medium">{user.username}</td>
                  <td className="px-4 py-3 text-dark-300">{user.email}</td>
                  <td className="px-4 py-3 text-center">
                    {user.is_admin ? (
                      <span className="text-xs bg-yellow-900/50 text-yellow-400 px-2 py-0.5 rounded-full">
                        Admin
                      </span>
                    ) : (
                      <span className="text-xs bg-dark-700 text-dark-400 px-2 py-0.5 rounded-full">
                        User
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full ${
                        user.is_active
                          ? "bg-green-900/50 text-green-400"
                          : "bg-red-900/50 text-red-400"
                      }`}
                    >
                      {user.is_active ? "Active" : "Disabled"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right text-dark-400 text-xs">
                    {new Date(user.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 text-center">
                    {user.id !== currentUser?.id && (
                      <button
                        onClick={() =>
                          toggleMutation.mutate({
                            userId: user.id,
                            isActive: !user.is_active,
                          })
                        }
                        className={`text-xs px-3 py-1 rounded ${
                          user.is_active
                            ? "btn-danger"
                            : "btn-primary"
                        }`}
                      >
                        {user.is_active ? "Disable" : "Enable"}
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
