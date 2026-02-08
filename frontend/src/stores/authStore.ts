import { create } from "zustand";
import type { User } from "../types";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  setUser: (user: User, accessToken: string, refreshToken: string) => void;
  logout: () => void;
  loadFromStorage: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,

  setUser: (user, accessToken, refreshToken) => {
    localStorage.setItem("access_token", accessToken);
    localStorage.setItem("refresh_token", refreshToken);
    localStorage.setItem("user", JSON.stringify(user));
    set({ user, isAuthenticated: true });
  },

  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user");
    set({ user: null, isAuthenticated: false });
  },

  loadFromStorage: () => {
    const token = localStorage.getItem("access_token");
    const userStr = localStorage.getItem("user");
    if (token && userStr) {
      try {
        const user = JSON.parse(userStr) as User;
        set({ user, isAuthenticated: true });
      } catch {
        set({ user: null, isAuthenticated: false });
      }
    }
  },
}));
