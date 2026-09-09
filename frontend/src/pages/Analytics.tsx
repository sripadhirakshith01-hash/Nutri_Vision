import { useEffect, useState, type ReactNode } from "react";
import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { getDashboard } from "../api/dashboard";
import { ApiError } from "../api/client";
import type { DashboardData } from "../types";
import { formatKcal } from "../utils/format";
import { goalLabel } from "../utils/nutrition";

export function AnalyticsPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getDashboard()
      .then(setData)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load analytics."));
  }, []);

  if (error) return <p className="text-clay">{error}</p>;
  if (!data) return <div className="skeleton h-80 rounded-3xl" />;

  const weekly = data.weekly_calories.map((item) => ({
    ...item,
    day: item.label || item.date.slice(5),
  }));

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-[0.2em] text-leaf">Trends</p>
        <h1 className="font-display mt-2 text-4xl">Analytics</h1>
        <p className="mt-2 max-w-2xl text-stone">
          Weekly calories and macros from meals you logged. Goal status is informational — not a prescription to eat
          less.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <article className="rounded-3xl border border-line bg-cream-soft p-5">
          <p className="text-sm text-stone">This week</p>
          <p className="mt-2 font-display text-3xl">{formatKcal(data.weekly_calories.reduce((sum, day) => sum + day.calories, 0))}</p>
        </article>
        <article className="rounded-3xl border border-line bg-cream-soft p-5">
          <p className="text-sm text-stone">Today vs target</p>
          <p className="mt-2 font-display text-3xl">{goalLabel(data.goal_status)}</p>
        </article>
        <article className="rounded-3xl border border-line bg-cream-soft p-5">
          <p className="text-sm text-stone">Meals today</p>
          <p className="mt-2 font-display text-3xl">{data.today.meals}</p>
        </article>
      </div>

      <ChartCard title="Weekly calories">
        {weekly.some((day) => day.calories > 0) ? (
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={weekly}>
              <CartesianGrid stroke="#e6dccb" vertical={false} />
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip formatter={(value) => formatKcal(Number(value))} />
              <Bar dataKey="calories" fill="#1b3d2f" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <EmptyChart text="Log meals this week to see calorie trends." />
        )}
      </ChartCard>

      <ChartCard title="Macronutrient trends">
        {weekly.some((day) => (day.protein_g ?? 0) + (day.carbs_g ?? 0) + (day.fat_g ?? 0) > 0) ? (
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={weekly}>
              <CartesianGrid stroke="#e6dccb" vertical={false} />
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="protein_g" name="Protein" stroke="#1b3d2f" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="carbs_g" name="Carbs" stroke="#3f7a58" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="fat_g" name="Fat" stroke="#d46a3a" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <EmptyChart text="Macro trends appear after you log a few days." />
        )}
      </ChartCard>

      <section className="space-y-3">
        <h2 className="font-display text-3xl">Insights from your log</h2>
        {data.insights.map((insight) => (
          <article key={insight.text} className="rounded-3xl border border-line bg-cream-soft p-5">
            <p>{insight.text}</p>
          </article>
        ))}
      </section>

      <p className="text-xs text-stone">
        These observations are calculated from saved meals. They are not medical advice and should not be used to pursue
        extreme calorie restriction.
      </p>
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-3xl border border-line bg-cream-soft p-5">
      <h2 className="mb-4 font-medium">{title}</h2>
      {children}
    </section>
  );
}

function EmptyChart({ text }: { text: string }) {
  return <p className="grid h-60 place-items-center text-sm text-stone">{text}</p>;
}
