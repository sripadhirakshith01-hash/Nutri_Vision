import { apiFetch } from "./client";
import type { User } from "../types";

export function getProfile() {
  return apiFetch<User>("/api/profile");
}

export function updateProfile(payload: Partial<User>) {
  return apiFetch<User>("/api/profile", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}
