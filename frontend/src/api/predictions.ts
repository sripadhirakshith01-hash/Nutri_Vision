import { apiFetch } from "./client";
import type { PredictResponse, PredictionItem } from "../types";

export function analyzeFood(file: File, estimatedGrams?: number, save = false) {
  const body = new FormData();
  body.append("image", file);
  body.append("save", String(save));
  if (estimatedGrams) body.append("estimated_grams", String(estimatedGrams));
  return apiFetch<PredictResponse>("/api/food/analyze", { method: "POST", body });
}

export function listPredictions(params?: { q?: string; date_from?: string; date_to?: string }) {
  const query = new URLSearchParams();
  if (params?.q) query.set("q", params.q);
  if (params?.date_from) query.set("date_from", params.date_from);
  if (params?.date_to) query.set("date_to", params.date_to);
  const suffix = query.toString() ? `?${query}` : "";
  return apiFetch<PredictionItem[]>(`/api/meals${suffix}`);
}

export function addMeal(payload: {
  food_name: string;
  estimated_grams: number;
  meal_type?: string;
  confidence?: number;
  image_path?: string | null;
}) {
  return apiFetch<PredictionItem>("/api/meals", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateMeal(
  id: number,
  payload: { estimated_grams?: number; food_name?: string; meal_type?: string },
) {
  return apiFetch<PredictionItem>(`/api/meals/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function updatePortion(id: number, estimatedGrams: number, foodName?: string) {
  return apiFetch<{
    prediction_id: number;
    estimated_grams: number;
    estimated: { calories: number; protein_g: number; carbs_g: number; fat_g: number; fiber_g?: number };
    meal?: PredictionItem;
  }>(`/api/predictions/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ estimated_grams: estimatedGrams, food_name: foodName ?? null }),
  });
}

export function deletePrediction(id: number) {
  return apiFetch<void>(`/api/meals/${id}`, { method: "DELETE" });
}

export function sendFeedback(id: number, correct: boolean, actualFood?: string) {
  return apiFetch(`/api/predictions/${id}/feedback`, {
    method: "POST",
    body: JSON.stringify({ correct, actual_food: actualFood || null }),
  });
}
