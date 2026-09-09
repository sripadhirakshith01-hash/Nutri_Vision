import { describe, expect, it } from "vitest";
import { goalLabel, scaleNutrition } from "./nutrition";

describe("scaleNutrition", () => {
  it("scales pizza macros from 100g to 250g", () => {
    const result = scaleNutrition(
      { protein_g: 12, carbs_g: 36, fat_g: 10, fiber_g: 2, calories: 285, serving_size: 100 },
      250,
    );
    expect(result.calories).toBe(712.5);
    expect(result.protein_g).toBe(30);
    expect(result.fiber_g).toBe(5);
  });
});

describe("goalLabel", () => {
  it("maps statuses without encouraging restriction copy", () => {
    expect(goalLabel("under_target")).toBe("Under target");
    expect(goalLabel("near_target")).toBe("Near target");
    expect(goalLabel("over_target")).toBe("Over target");
  });
});
