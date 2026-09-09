import { Camera, History, MessageCircle, Plus } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { getDashboard } from "../api/dashboard";
import { ApiError } from "../api/client";
import type { DashboardData, PredictionItem } from "../types";
import { foodEmoji, formatKcal } from "../utils/format";
import { goalLabel } from "../utils/nutrition";

const MEAL_ORDER = ["breakfast", "lunch", "snack", "dinner"];

export function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getDashboard()
      .then(setData)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load dashboard."));
  }, []);

  const grouped = useMemo(() => groupMeals(data?.today_meals ?? []), [data]);

  if (error) return <p className="text-clay">{error}</p>;
  if (!data) return <div className="skeleton h-80 rounded-3xl" />;

  const target = data.targets?.calories ?? null;
  const consumed = data.today.calories;
  const remaining = data.remaining?.calories;
  const pct = target ? Math.min(100, (consumed / target) * 100) : 0;

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-sm uppercase tracking-[0.2em] text-leaf">Today</p>
          <h1 className="font-display mt-2 text-4xl">Dashboard</h1>
        </div>
        <p className="rounded-full bg-forest/8 px-3 py-1 text-sm text-forest">{goalLabel(data.goal_status)}</p>
      </div>

      <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
        <article className="grid place-items-center rounded-[32px] border border-line bg-cream-soft p-6">
          <CalorieRing consumed={consumed} target={target} percent={pct} />
          <div className="mt-4 grid w-full grid-cols-3 gap-2 text-center text-xs">
            <Stat label="Target" value={target ? `${target}` : "—"} />
            <Stat label="Consumed" value={`${Math.round(consumed)}`} />
            <Stat label="Remaining" value={remaining == null ? "—" : `${Math.round(remaining)}`} />
          </div>
        </article>

        <div className="grid gap-4 sm:grid-cols-3">
          <MacroCard label="Protein" value={data.today.protein_g} target={data.targets?.protein_g} />
          <MacroCard label="Carbohydrates" value={data.today.carbs_g} target={data.targets?.carbs_g} />
          <MacroCard label="Fat" value={data.today.fat_g} target={data.targets?.fat_g} />
          <div className="grid grid-cols-2 gap-3 sm:col-span-3">
            <QuickLink to="/analyze" icon={Camera} label="Analyze Food" />
            <QuickLink to="/analyze" icon={Plus} label="Add Meal" />
            <QuickLink to="/chat" icon={MessageCircle} label="Ask AI" />
            <QuickLink to="/meals" icon={History} label="View History" />
          </div>
        </div>
      </div>

      <section className="rounded-[32px] border border-line bg-cream-soft p-6">
        <div className="flex items-center justify-between">
          <h2 className="font-display text-2xl">Today's meals</h2>
          <Link to="/analyze" className="text-sm text-forest hover:underline">
            + Add meal
          </Link>
        </div>
        <div className="mt-5 grid gap-5 md:grid-cols-2">
          {MEAL_ORDER.map((slot) => (
            <div key={slot}>
              <p className="text-xs uppercase tracking-[0.16em] text-stone">{slot}</p>
              <div className="mt-2 space-y-2">
                {(grouped[slot] ?? []).length === 0 ? (
                  <p className="rounded-2xl border border-dashed border-line px-3 py-4 text-sm text-stone">No meals yet</p>
                ) : (
                  grouped[slot].map((meal) => (
                    <div key={meal.prediction_id} className="flex items-center justify-between rounded-2xl bg-cream px-3 py-3">
                      <p>
                        {foodEmoji(meal.food_name)} {meal.display_name}
                      </p>
                      <p className="text-sm font-medium">{formatKcal(meal.estimated_calories)}</p>
                    </div>
                  ))
                )}
              </div>
            </div>
          ))}
        </div>
      </section>

      <p className="text-xs text-stone">
        Daily targets use the Mifflin-St Jeor estimate from your profile. Nutrition values are estimates and may vary
        based on ingredients, preparation method, and portion size.
      </p>
    </div>
  );
}

function groupMeals(meals: PredictionItem[]) {
  const map: Record<string, PredictionItem[]> = {};
  for (const meal of meals) {
    const key = meal.meal_type || "snack";
    map[key] = [...(map[key] ?? []), meal];
  }
  return map;
}

function CalorieRing({ consumed, target, percent }: { consumed: number; target: number | null; percent: number }) {
  return (
    <div className="relative grid h-48 w-48 place-items-center">
      <div
        className="absolute inset-0 rounded-full"
        style={{ background: `conic-gradient(#3f7a58 ${percent}%, #e6dccb 0)` }}
      />
      <div className="absolute inset-[14px] rounded-full bg-cream-soft" />
      <div className="relative text-center">
        <p className="font-display text-3xl">{Math.round(consumed).toLocaleString()}</p>
        <p className="text-sm text-stone">/ {target ? target.toLocaleString() : "—"} kcal</p>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-stone">{label}</p>
      <p className="mt-1 font-medium">{value}</p>
    </div>
  );
}

function MacroCard({ label, value, target }: { label: string; value: number; target?: number }) {
  const pct = target ? Math.min(100, (value / target) * 100) : 0;
  return (
    <article className="rounded-[28px] border border-line bg-cream-soft p-5">
      <p className="text-sm text-stone">{label}</p>
      <p className="mt-2 font-display text-2xl">
        {Math.round(value)}
        {target ? <span className="text-base text-stone"> / {target} g</span> : <span className="text-base text-stone"> g</span>}
      </p>
      <div className="mt-3 h-2 overflow-hidden rounded-full bg-line">
        <div className="h-full rounded-full bg-leaf" style={{ width: `${pct}%` }} />
      </div>
    </article>
  );
}

function QuickLink({ to, icon: Icon, label }: { to: string; icon: typeof Camera; label: string }) {
  return (
    <Link to={to} className="flex items-center gap-3 rounded-2xl border border-line bg-cream px-4 py-3 text-sm hover:border-forest/30">
      <Icon size={16} className="text-leaf" />
      {label}
    </Link>
  );
}
