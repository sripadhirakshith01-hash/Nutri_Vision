import { apiFetch, setToken } from "./client";
import type { AuthResponse, User } from "../types";

export async function register(name: string, email: string, password: string) {
  const data = await apiFetch<AuthResponse>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify({ name, email, password }),
  });
  setToken(data.access_token);
  return data;
}

export async function login(email: string, password: string) {
  const data = await apiFetch<AuthResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  setToken(data.access_token);
  return data;
}

export function logout() {
  setToken(null);
  localStorage.removeItem("nourish.user");
}

export function me() {
  return apiFetch<User>("/api/auth/me");
}
