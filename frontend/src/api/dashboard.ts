import { apiFetch } from "./client";
import type { DashboardData } from "../types";

export function getDashboard() {
  return apiFetch<DashboardData>("/api/dashboard");
}

export function getNutritionSummary() {
  return apiFetch("/api/nutrition/summary");
}
