import client from "./client";
import type { InviteCode, Marketplace, ScrapeJob, User } from "../types";

export async function getUsers(): Promise<User[]> {
  const { data } = await client.get<User[]>("/admin/users");
  return data;
}

export async function toggleUserActive(userId: string, isActive: boolean) {
  const { data } = await client.patch(`/admin/users/${userId}/toggle`, null, {
    params: { is_active: isActive },
  });
  return data;
}

export async function getInviteCodes(): Promise<InviteCode[]> {
  const { data } = await client.get<InviteCode[]>("/admin/invite-codes");
  return data;
}

export async function createInviteCode(maxUses: number = 1, grantsAdmin: boolean = false): Promise<InviteCode> {
  const { data } = await client.post<InviteCode>("/admin/invite-codes", {
    max_uses: maxUses,
    grants_admin: grantsAdmin,
  });
  return data;
}

export async function deleteInviteCode(codeId: string) {
  const { data } = await client.delete(`/admin/invite-codes/${codeId}`);
  return data;
}

export async function updateMarketplace(id: number, update: { is_enabled?: boolean; scrape_interval_minutes?: number }): Promise<Marketplace> {
  const { data } = await client.patch<Marketplace>(`/admin/marketplaces/${id}`, update);
  return data;
}

export async function getScrapeJobs(marketplaceId?: number): Promise<ScrapeJob[]> {
  const params = marketplaceId ? { marketplace_id: marketplaceId } : {};
  const { data } = await client.get<ScrapeJob[]>("/admin/scrape-jobs", { params });
  return data;
}

export async function getMarketplaces(): Promise<Marketplace[]> {
  const { data } = await client.get<Marketplace[]>("/marketplaces");
  return data;
}
