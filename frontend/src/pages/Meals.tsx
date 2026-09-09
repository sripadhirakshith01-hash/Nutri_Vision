import { Search, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { listFoods } from "../api/foods";
import { deletePrediction, listPredictions, updateMeal } from "../api/predictions";
import { ApiError } from "../api/client";
import { Button } from "../components/ui/button";
import { Input, Label, Select } from "../components/ui/input";
import type { FoodItem, PredictionItem } from "../types";
import { foodEmoji, formatDay, formatKcal, formatTime } from "../utils/format";

export function MealsPage() {
  const [items, setItems] = useState<PredictionItem[]>([]);
  const [foods, setFoods] = useState<FoodItem[]>([]);
  const [q, setQ] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<PredictionItem | null>(null);
  const [grams, setGrams] = useState(100);
  const [foodName, setFoodName] = useState("");
  const [mealType, setMealType] = useState("snack");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  async function load() {
    setLoading(true);
    setError("");
    try {
      setItems(await listPredictions({ q, date_from: dateFrom || undefined, date_to: dateTo || undefined }));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load meals.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
    listFoods()
      .then(setFoods)
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    if (!selected) return;
    setGrams(selected.estimated_grams || 100);
    setFoodName(selected.food_name);
    setMealType(selected.meal_type || "snack");
  }, [selected]);

  const groups = useMemo(() => {
    const map = new Map<string, PredictionItem[]>();
    for (const item of items) {
      const key = formatDay(item.predicted_at);
      map.set(key, [...(map.get(key) ?? []), item]);
    }
    return [...map.entries()];
  }, [items]);

  async function remove(id: number) {
    await deletePrediction(id);
    setItems((current) => current.filter((item) => item.prediction_id !== id));
    if (selected?.prediction_id === id) setSelected(null);
  }

  async function save() {
    if (!selected) return;
    setSaving(true);
    setError("");
    try {
      const updated = await updateMeal(selected.prediction_id, {
        estimated_grams: grams,
        food_name: foodName,
        meal_type: mealType,
      });
      setSelected(updated);
      setItems((current) => current.map((item) => (item.prediction_id === updated.prediction_id ? updated : item)));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not update this meal.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-[0.2em] text-leaf">History</p>
        <h1 className="font-display mt-2 text-4xl">Meal history</h1>
      </div>

      <div className="grid gap-3 rounded-3xl border border-line bg-cream-soft p-4 md:grid-cols-[1fr_auto_auto_auto]">
        <div className="relative">
          <Search className="absolute left-3 top-3.5 text-stone" size={16} />
          <Input className="pl-9" placeholder="Search foods" value={q} onChange={(event) => setQ(event.target.value)} />
        </div>
        <Input type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
        <Input type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
        <Button onClick={() => void load()}>Filter</Button>
      </div>

      {error ? <p className="text-sm text-clay">{error}</p> : null}
      {loading ? <div className="skeleton h-40 rounded-3xl" /> : null}

      {!loading && items.length === 0 ? (
        <div className="rounded-3xl border border-line bg-cream-soft p-10 text-center text-stone">
          No meals logged yet. Analyze a food photo to start your history.
        </div>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
        <div className="space-y-6">
          {groups.map(([day, meals]) => (
            <section key={day}>
              <h2 className="font-display text-2xl">{day}</h2>
              <div className="mt-3 space-y-3">
                {meals.map((meal) => (
                  <button
                    key={meal.prediction_id}
                    type="button"
                    onClick={() => setSelected(meal)}
                    className="flex w-full items-center justify-between rounded-3xl border border-line bg-cream-soft px-4 py-4 text-left hover:border-forest/30"
                  >
                    <div>
                      <p className="text-xs capitalize text-stone">
                        {meal.meal_type || "meal"} · {formatTime(meal.predicted_at)}
                      </p>
                      <p className="mt-1 text-lg">
                        {foodEmoji(meal.food_name)} {meal.display_name}
                      </p>
                    </div>
                    <p className="font-medium">{formatKcal(meal.estimated_calories)}</p>
                  </button>
                ))}
              </div>
            </section>
          ))}
        </div>

        <aside className="rounded-3xl border border-line bg-cream-soft p-5">
          {selected ? (
            <div className="space-y-3">
              <h3 className="font-display text-2xl">{selected.display_name}</h3>
              <p className="text-sm text-stone">{new Date(selected.predicted_at).toLocaleString()}</p>
              <p className="text-sm">Confidence: {selected.confidence.toFixed(0)}%</p>
              <div>
                <Label htmlFor="editFood">Detected food</Label>
                <Select id="editFood" value={foodName} onChange={(event) => setFoodName(event.target.value)}>
                  {foods.map((item) => (
                    <option key={item.food_name} value={item.food_name}>
                      {item.display_name}
                    </option>
                  ))}
                </Select>
              </div>
              <div>
                <Label htmlFor="editGrams">Serving size (g)</Label>
                <Input
                  id="editGrams"
                  type="number"
                  min={10}
                  max={2000}
                  value={grams}
                  onChange={(event) => setGrams(Number(event.target.value))}
                />
              </div>
              <div>
                <Label htmlFor="editMeal">Meal</Label>
                <Select id="editMeal" value={mealType} onChange={(event) => setMealType(event.target.value)}>
                  <option value="breakfast">Breakfast</option>
                  <option value="lunch">Lunch</option>
                  <option value="snack">Snack</option>
                  <option value="dinner">Dinner</option>
                </Select>
              </div>
              <p className="text-sm">
                Estimated: {formatKcal(selected.estimated_calories)} · Protein {selected.protein_g ?? "—"}g · Carbs{" "}
                {selected.carbs_g ?? "—"}g · Fat {selected.fat_g ?? "—"}g · Fiber {selected.fiber_g ?? "—"}g
              </p>
              <Button className="w-full" disabled={saving} onClick={() => void save()}>
                {saving ? "Saving..." : "Save changes"}
              </Button>
              <Button variant="danger" className="w-full" onClick={() => void remove(selected.prediction_id)}>
                <Trash2 size={16} /> Delete meal
              </Button>
            </div>
          ) : (
            <p className="text-stone">Select an entry to edit serving size, change the food, or view nutrition details.</p>
          )}
        </aside>
      </div>
    </div>
  );
}
