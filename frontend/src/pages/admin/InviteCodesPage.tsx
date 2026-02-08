import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getInviteCodes, createInviteCode, deleteInviteCode } from "../../api/admin";
import { Plus, Trash2, Copy } from "lucide-react";

export default function InviteCodesPage() {
  const queryClient = useQueryClient();
  const [maxUses, setMaxUses] = useState(1);
  const [grantsAdmin, setGrantsAdmin] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);

  const { data: codes, isLoading } = useQuery({
    queryKey: ["invite-codes"],
    queryFn: getInviteCodes,
  });

  const createMutation = useMutation({
    mutationFn: () => createInviteCode(maxUses, grantsAdmin),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["invite-codes"] });
      setMaxUses(1);
      setGrantsAdmin(false);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteInviteCode,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["invite-codes"] }),
  });

  const copyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopied(code);
    setTimeout(() => setCopied(null), 2000);
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Invite Codes</h1>

      {/* Create New */}
      <div className="card">
        <h2 className="font-semibold mb-4">Generate New Invite Code</h2>
        <div className="flex items-end gap-4">
          <div>
            <label className="block text-xs text-dark-400 mb-1">Max Uses</label>
            <input
              type="number"
              min={1}
              max={100}
              value={maxUses}
              onChange={(e) => setMaxUses(Number(e.target.value))}
              className="input w-24"
            />
          </div>
          <label className="flex items-center gap-2 text-sm text-dark-300 pb-2">
            <input
              type="checkbox"
              checked={grantsAdmin}
              onChange={(e) => setGrantsAdmin(e.target.checked)}
              className="accent-primary-500"
            />
            Grants Admin
          </label>
          <button
            onClick={() => createMutation.mutate()}
            disabled={createMutation.isPending}
            className="btn-primary flex items-center gap-2"
          >
            <Plus size={16} />
            Generate
          </button>
        </div>
      </div>

      {/* List */}
      <div className="card p-0 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-dark-700">
              <th className="text-left px-4 py-3 text-dark-400 font-medium">Code</th>
              <th className="text-center px-4 py-3 text-dark-400 font-medium">Uses</th>
              <th className="text-center px-4 py-3 text-dark-400 font-medium">Admin</th>
              <th className="text-center px-4 py-3 text-dark-400 font-medium">Status</th>
              <th className="text-right px-4 py-3 text-dark-400 font-medium">Created</th>
              <th className="text-center px-4 py-3 text-dark-400 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={6} className="text-center py-8 text-dark-400">Loading...</td>
              </tr>
            ) : (
              codes?.map((code) => (
                <tr key={code.id} className="border-b border-dark-800 hover:bg-dark-800/50">
                  <td className="px-4 py-3 font-mono font-medium">{code.code}</td>
                  <td className="px-4 py-3 text-center">
                    {code.times_used} / {code.max_uses}
                  </td>
                  <td className="px-4 py-3 text-center">
                    {code.grants_admin ? (
                      <span className="text-yellow-400 text-xs">Yes</span>
                    ) : (
                      <span className="text-dark-500 text-xs">No</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full ${
                        code.is_active
                          ? "bg-green-900/50 text-green-400"
                          : "bg-red-900/50 text-red-400"
                      }`}
                    >
                      {code.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right text-dark-400 text-xs">
                    {new Date(code.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <div className="flex items-center justify-center gap-2">
                      <button
                        onClick={() => copyCode(code.code)}
                        className="text-dark-400 hover:text-primary-400"
                        title="Copy"
                      >
                        {copied === code.code ? (
                          <span className="text-xs text-green-400">Copied!</span>
                        ) : (
                          <Copy size={14} />
                        )}
                      </button>
                      {code.is_active && (
                        <button
                          onClick={() => deleteMutation.mutate(code.id)}
                          className="text-dark-400 hover:text-red-400"
                          title="Deactivate"
                        >
                          <Trash2 size={14} />
                        </button>
                      )}
                    </div>
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
