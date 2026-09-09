import { AlertTriangle, Camera, Check, Minus, Plus, Trash2, Upload } from "lucide-react";
import { useEffect, useMemo, useRef, useState, type DragEvent } from "react";
import { useNavigate } from "react-router-dom";
import { listFoods } from "../api/foods";
import { addMeal, analyzeFood } from "../api/predictions";
import { ApiError } from "../api/client";
import { Button } from "../components/ui/button";
import { Input, Label, Select } from "../components/ui/input";
import type { FoodItem, PredictResponse } from "../types";
import { foodEmoji, formatGrams, formatKcal } from "../utils/format";
import { scaleNutrition } from "../utils/nutrition";

const STEPS = ["Reading image", "Running Food-101 model", "Looking up nutrition", "Ready to log"];
const MAX_MB = 8;

export function AnalyzePage() {
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [grams, setGrams] = useState(100);
  const [mealType, setMealType] = useState("lunch");
  const [busy, setBusy] = useState(false);
  const [saving, setSaving] = useState(false);
  const [step, setStep] = useState(0);
  const [error, setError] = useState("");
  const [result, setResult] = useState<PredictResponse | null>(null);
  const [foods, setFoods] = useState<FoodItem[]>([]);
  const [selectedFood, setSelectedFood] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    listFoods()
      .then(setFoods)
      .catch(() => undefined);
  }, []);

  const catalogFood = useMemo(
    () => foods.find((item) => item.food_name === selectedFood) ?? null,
    [foods, selectedFood],
  );

  const per100 = catalogFood
    ? {
        protein_g: catalogFood.protein_g ?? 0,
        carbs_g: catalogFood.carbs_g ?? 0,
        fat_g: catalogFood.fat_g ?? 0,
        fiber_g: catalogFood.fiber_g ?? 0,
        calories: catalogFood.calories ?? 0,
        serving_size: catalogFood.serving_size || 100,
      }
    : result?.nutrition_per_100g;

  const estimated = per100 ? scaleNutrition(per100, grams) : null;

  function setImage(next: File | null) {
    setResult(null);
    setSaved(false);
    setError("");
    setFile(next);
    if (preview) URL.revokeObjectURL(preview);
    setPreview(next ? URL.createObjectURL(next) : null);
  }

  function onDrop(event: DragEvent<HTMLElement>) {
    event.preventDefault();
    const next = event.dataTransfer.files[0];
    if (next) validateAndSet(next);
  }

  function validateAndSet(next: File) {
    const okType = ["image/jpeg", "image/png", "image/webp", "image/jpg"].includes(next.type) || /\.(jpe?g|png|webp)$/i.test(next.name);
    if (!okType) {
      setError("Unsupported image format. Use JPG, JPEG, PNG, or WebP.");
      return;
    }
    if (next.size > MAX_MB * 1024 * 1024) {
      setError(`Image is too large. Maximum size is ${MAX_MB} MB.`);
      return;
    }
    setImage(next);
  }

  async function analyze() {
    if (!file) {
      setError("Upload a food image first.");
      return;
    }
    setBusy(true);
    setError("");
    setSaved(false);
    setStep(0);
    const timer = window.setInterval(() => setStep((value) => Math.min(value + 1, 2)), 700);
    try {
      const data = await analyzeFood(file, undefined, false);
      setStep(3);
      setResult(data);
      setSelectedFood(data.food_name);
      if (data.meal_type) setMealType(data.meal_type);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Analysis failed. Please try another image.");
    } finally {
      window.clearInterval(timer);
      setBusy(false);
    }
  }

  async function addToLog() {
    if (!result || !selectedFood) return;
    setSaving(true);
    setError("");
    try {
      await addMeal({
        food_name: selectedFood,
        estimated_grams: grams,
        meal_type: mealType,
        confidence: result.confidence,
        image_path: result.image_path,
      });
      setSaved(true);
      window.setTimeout(() => navigate("/dashboard"), 700);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not add this meal to today's log.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <p className="text-sm uppercase tracking-[0.2em] text-leaf">Recognition</p>
        <h1 className="font-display mt-2 text-4xl">Analyze your food</h1>
        <p className="mt-2 text-stone">Upload a photo. The existing Food-101 model identifies the dish.</p>
      </div>

      <section
        onDragOver={(event) => event.preventDefault()}
        onDrop={onDrop}
        className="rounded-[32px] border border-dashed border-forest/25 bg-cream-soft p-6 text-center"
      >
        {preview ? (
          <div className="space-y-4">
            <img src={preview} alt="Food preview" className="mx-auto max-h-80 rounded-3xl object-cover" />
            <div className="flex justify-center gap-3">
              <Button variant="secondary" onClick={() => inputRef.current?.click()}>
                Replace image
              </Button>
              <Button variant="ghost" onClick={() => setImage(null)}>
                <Trash2 size={16} /> Remove
              </Button>
            </div>
          </div>
        ) : (
          <button type="button" onClick={() => inputRef.current?.click()} className="w-full py-16">
            <Camera className="mx-auto text-leaf" size={36} />
            <p className="mt-4 text-lg font-medium">Upload your food</p>
            <p className="mt-2 flex items-center justify-center gap-2 text-stone">
              <Upload size={16} /> Drag & drop or browse image
            </p>
            <p className="mt-2 text-xs text-stone">JPG, JPEG, PNG, or WebP · up to {MAX_MB} MB</p>
          </button>
        )}
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          className="hidden"
          onChange={(event) => event.target.files?.[0] && validateAndSet(event.target.files[0])}
        />
      </section>

      <Button className="w-full" size="lg" disabled={busy} onClick={() => void analyze()}>
        {busy && !result ? "Analyzing your food..." : "Analyze Food"}
      </Button>

      {busy && !result ? (
        <div className="rounded-3xl border border-line bg-cream-soft p-5">
          <p className="font-medium">Analyzing your food...</p>
          <ul className="mt-4 space-y-2 text-sm">
            {STEPS.map((label, index) => (
              <li key={label} className={index <= step ? "text-forest" : "text-stone"}>
                {index <= step ? "✓" : "○"} {label}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {error ? <p className="rounded-2xl bg-clay/10 px-4 py-3 text-sm text-clay">{error}</p> : null}

      {result ? (
        <section className="fade-up space-y-5 rounded-[32px] border border-line bg-cream-soft p-6">
          <div>
            <p className="text-sm text-stone">Food detected</p>
            <h2 className="font-display mt-1 text-4xl">
              {foodEmoji(selectedFood || result.food_name)} {catalogFood?.display_name || result.display_name}
            </h2>
            <p className="mt-2 text-stone">{result.confidence.toFixed(0)}% confidence</p>
            <div className="mt-3 h-2 overflow-hidden rounded-full bg-line">
              <div className="h-full bg-forest" style={{ width: `${Math.min(result.confidence, 100)}%` }} />
            </div>
          </div>

          {result.low_confidence ? (
            <div className="flex gap-3 rounded-2xl bg-clay/10 p-4 text-sm text-ink">
              <AlertTriangle className="shrink-0 text-clay" />
              <div>
                <p className="font-medium">We're not completely confident about this prediction.</p>
                <p className="mt-1 text-stone">
                  Possible food: {result.display_name} · {result.confidence.toFixed(0)}% confidence. Please verify the
                  food before adding it to your nutrition log.
                </p>
              </div>
            </div>
          ) : null}

          <div>
            <Label htmlFor="food">Is this correct?</Label>
            <Select id="food" value={selectedFood} onChange={(event) => setSelectedFood(event.target.value)}>
              {result.top_predictions.map((item) => (
                <option key={item.food} value={item.food}>
                  {item.display_name} ({item.confidence.toFixed(0)}%)
                </option>
              ))}
              {foods
                .filter((item) => !result.top_predictions.some((top) => top.food === item.food_name))
                .map((item) => (
                  <option key={item.food_name} value={item.food_name}>
                    {item.display_name}
                  </option>
                ))}
            </Select>
          </div>

          <div className="rounded-3xl bg-cream p-4">
            <p className="text-sm text-stone">Serving size</p>
            <div className="mt-3 flex items-center justify-center gap-3">
              <Button variant="secondary" size="icon" onClick={() => setGrams((value) => Math.max(10, value - 10))}>
                <Minus size={16} />
              </Button>
              <div className="flex items-center gap-2">
                <Input
                  type="number"
                  min={10}
                  max={2000}
                  value={grams}
                  onChange={(event) => setGrams(Number(event.target.value))}
                  className="w-28 text-center"
                />
                <span className="text-stone">g</span>
              </div>
              <Button variant="secondary" size="icon" onClick={() => setGrams((value) => Math.min(2000, value + 10))}>
                <Plus size={16} />
              </Button>
            </div>
          </div>

          <div>
            <Label htmlFor="mealType">Meal</Label>
            <Select id="mealType" value={mealType} onChange={(event) => setMealType(event.target.value)}>
              <option value="breakfast">Breakfast</option>
              <option value="lunch">Lunch</option>
              <option value="snack">Snack</option>
              <option value="dinner">Dinner</option>
            </Select>
          </div>

          {result.nutrition_missing && !catalogFood ? (
            <p className="text-sm text-clay">Nutrition data is unavailable for this food.</p>
          ) : null}

          {estimated ? (
            <div>
              <h3 className="font-display text-2xl">Estimated nutrition</h3>
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <NutritionTile label="Calories" value={formatKcal(estimated.calories)} accent />
                <NutritionTile label="Protein" value={formatGrams(estimated.protein_g)} />
                <NutritionTile label="Carbs" value={formatGrams(estimated.carbs_g)} />
                <NutritionTile label="Fat" value={formatGrams(estimated.fat_g)} />
                <NutritionTile label="Fiber" value={formatGrams(estimated.fiber_g)} />
              </div>
              <p className="mt-3 text-xs text-stone">
                Nutrition values are estimates and may vary based on ingredients, preparation method, and portion size.
              </p>
            </div>
          ) : null}

          <Button className="w-full" size="lg" disabled={saving || saved} onClick={() => void addToLog()}>
            {saved ? (
              <>
                <Check size={16} /> Added to today's log
              </>
            ) : saving ? (
              "Saving..."
            ) : (
              "Add to Today's Log"
            )}
          </Button>
        </section>
      ) : null}
    </div>
  );
}

function NutritionTile({ label, value, accent = false }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className={`rounded-3xl p-4 ${accent ? "bg-forest text-cream-soft" : "bg-white"}`}>
      <p className={`text-sm ${accent ? "text-cream/70" : "text-stone"}`}>{label}</p>
      <p className="mt-2 font-display text-3xl">{value}</p>
    </div>
  );
}
