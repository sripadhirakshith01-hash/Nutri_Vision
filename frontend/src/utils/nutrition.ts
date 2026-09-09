export function scaleNutrition(
  per100: { protein_g: number; carbs_g: number; fat_g: number; fiber_g?: number; calories: number; serving_size: number },
  grams: number,
) {
  const factor = grams / (per100.serving_size || 100);
  const round1 = (value: number) => Math.round(value * 10) / 10;
  return {
    protein_g: round1(per100.protein_g * factor),
    carbs_g: round1(per100.carbs_g * factor),
    fat_g: round1(per100.fat_g * factor),
    fiber_g: round1((per100.fiber_g ?? 0) * factor),
    calories: round1(per100.calories * factor),
    serving_size: grams,
    basis: `estimated ${grams}g serving`,
  };
}

export function goalLabel(status: string | null | undefined) {
  if (status === "under_target") return "Under target";
  if (status === "near_target") return "Near target";
  if (status === "over_target") return "Over target";
  return "No target yet";
}
