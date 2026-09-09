import { apiFetch } from "./client";
import type { FoodItem } from "../types";

export function listFoods(q?: string) {
  const suffix = q ? `?q=${encodeURIComponent(q)}` : "";
  return apiFetch<FoodItem[]>(`/api/foods${suffix}`);
}
