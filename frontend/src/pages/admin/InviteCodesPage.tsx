import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getInviteCodes, createInviteCode, deleteInviteCode } from "../../api/admin";
import { Plus, Trash2, Copy, KeyRound, Check } from "lucide-react";
import clsx from "clsx";

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
      {/* Header */}
      <div className="flex items-center gap-3 animate-fade-in">
        <div className="p-2.5 rounded-xl bg-amber-500/10">
          <KeyRound size={22} className="text-amber-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Invite Codes</h1>
          <p className="text-dark-400 text-sm mt-0.5">
            <span className="text-primary-400 font-semibold">{codes?.filter((c) => c.is_active).length ?? 0}</span> active codes
          </p>
        </div>
      </div>

      {/* Create New */}
      <div className="card animate-slide-up">
        <h2 className="font-medium text-sm mb-5 flex items-center gap-2">
          <Plus size={16} className="text-primary-400" />
          Generate New Invite Code
        </h2>
        <div className="flex items-end gap-4 flex-wrap">
          <div>
            <label className="block text-[10px] text-dark-500 font-medium uppercase tracking-wider mb-1.5">Max Uses</label>
            <input
              type="number"
              min={1}
              max={100}
              value={maxUses}
              onChange={(e) => setMaxUses(Number(e.target.value))}
              className="input w-24 text-sm"
            />
          </div>
          <label className="flex items-center gap-2.5 text-sm text-dark-300 pb-2.5 cursor-pointer">
            <input
              type="checkbox"
              checked={grantsAdmin}
              onChange={(e) => setGrantsAdmin(e.target.checked)}
              className="accent-primary-500 w-4 h-4"
            />
            Grants Admin
          </label>
          <button
            onClick={() => createMutation.mutate()}
            disabled={createMutation.isPending}
            className="btn-primary flex items-center gap-2 text-sm"
          >
            {createMutation.isPending ? (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <Plus size={16} />
            )}
            Generate
          </button>
        </div>
      </div>

      {/* List */}
      <div className="card overflow-x-auto p-0 animate-slide-up" style={{ animationDelay: "100ms" }}>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-dark-700/50">
              <th className="text-left px-5 py-4 text-[10px] text-dark-500 font-semibold uppercase tracking-wider">Code</th>
              <th className="text-center px-4 py-4 text-[10px] text-dark-500 font-semibold uppercase tracking-wider">Uses</th>
              <th className="text-center px-4 py-4 text-[10px] text-dark-500 font-semibold uppercase tracking-wider">Admin</th>
              <th className="text-center px-4 py-4 text-[10px] text-dark-500 font-semibold uppercase tracking-wider">Status</th>
              <th className="text-right px-4 py-4 text-[10px] text-dark-500 font-semibold uppercase tracking-wider">Created</th>
              <th className="text-center px-4 py-4 text-[10px] text-dark-500 font-semibold uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={6} className="text-center py-16">
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-8 h-8 border-2 border-primary-500/30 border-t-primary-500 rounded-full animate-spin" />
                    <span className="text-dark-400 text-sm">Loading codes...</span>
                  </div>
                </td>
              </tr>
            ) : (
              codes?.map((code, i) => (
                <tr
                  key={code.id}
                  className="border-b border-dark-700/20 table-row-hover animate-fade-in"
                  style={{ animationDelay: `${i * 20}ms` }}
                >
                  <td className="px-5 py-3.5 font-mono font-medium text-dark-200 text-xs">{code.code}</td>
                  <td className="px-4 py-3.5 text-center">
                    <span className="font-mono text-dark-300">
                      {code.times_used} <span className="text-dark-600">/</span> {code.max_uses}
                    </span>
                  </td>
                  <td className="px-4 py-3.5 text-center">
                    {code.grants_admin ? (
                      <span className="text-[10px] font-semibold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded-md border border-amber-500/20">
                        Admin
                      </span>
                    ) : (
                      <span className="text-dark-500 text-xs">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3.5 text-center">
                    <span
                      className={clsx(
                        "text-[10px] font-semibold px-2.5 py-1 rounded-lg uppercase tracking-wider border",
                        code.is_active
                          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                          : "bg-red-500/10 text-red-400 border-red-500/20"
                      )}
                    >
                      {code.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="px-4 py-3.5 text-right text-dark-500 text-xs font-mono">
                    {new Date(code.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3.5 text-center">
                    <div className="flex items-center justify-center gap-1.5">
                      <button
                        onClick={() => copyCode(code.code)}
                        className="p-2 rounded-lg text-dark-400 hover:text-primary-400 hover:bg-primary-500/10 transition-all"
                        title="Copy"
                      >
                        {copied === code.code ? (
                          <Check size={14} className="text-emerald-400" />
                        ) : (
                          <Copy size={14} />
                        )}
                      </button>
                      {code.is_active && (
                        <button
                          onClick={() => deleteMutation.mutate(code.id)}
                          className="p-2 rounded-lg text-dark-400 hover:text-red-400 hover:bg-red-500/10 transition-all"
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
