import { useEffect, useState, type FormEvent } from "react";
import { updateProfile } from "../api/profile";
import { ApiError } from "../api/client";
import { Button } from "../components/ui/button";
import { Input, Label, Select } from "../components/ui/input";
import { useAuth } from "../hooks/useAuth";

export function ProfilePage() {
  const { user, refresh } = useAuth();
  const [form, setForm] = useState({
    name: "",
    age: "",
    gender: "",
    height: "",
    weight: "",
    activity_level: "",
    goal: "",
  });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!user) return;
    setForm({
      name: user.name ?? "",
      age: user.age?.toString() ?? "",
      gender: user.gender ?? "",
      height: user.height?.toString() ?? "",
      weight: user.weight?.toString() ?? "",
      activity_level: user.activity_level ?? "",
      goal: user.goal ?? "",
    });
  }, [user]);

  function set<K extends keyof typeof form>(key: K, value: string) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await updateProfile({
        name: form.name,
        age: form.age ? Number(form.age) : null,
        gender: form.gender || null,
        height: form.height ? Number(form.height) : null,
        weight: form.weight ? Number(form.weight) : null,
        activity_level: form.activity_level || null,
        goal: form.goal || null,
      });
      await refresh();
      setMessage("Profile saved.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save profile.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <p className="text-sm uppercase tracking-[0.2em] text-leaf">Account</p>
        <h1 className="font-display mt-2 text-4xl">Profile</h1>
      </div>

      <form onSubmit={onSubmit} className="space-y-4 rounded-[32px] border border-line bg-cream-soft p-6">
        <div>
          <Label htmlFor="name">Name</Label>
          <Input id="name" value={form.name} onChange={(e) => set("name", e.target.value)} required />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <Label htmlFor="age">Age</Label>
            <Input id="age" type="number" value={form.age} onChange={(e) => set("age", e.target.value)} />
          </div>
          <div>
            <Label htmlFor="gender">Gender</Label>
            <Select id="gender" value={form.gender} onChange={(e) => set("gender", e.target.value)}>
              <option value="">Select</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
              <option value="prefer_not_to_say">Prefer not to say</option>
            </Select>
          </div>
          <div>
            <Label htmlFor="height">Height (cm)</Label>
            <Input id="height" type="number" value={form.height} onChange={(e) => set("height", e.target.value)} />
          </div>
          <div>
            <Label htmlFor="weight">Weight (kg)</Label>
            <Input id="weight" type="number" value={form.weight} onChange={(e) => set("weight", e.target.value)} />
          </div>
          <div>
            <Label htmlFor="activity">Activity level</Label>
            <Select id="activity" value={form.activity_level} onChange={(e) => set("activity_level", e.target.value)}>
              <option value="">Select</option>
              <option value="sedentary">Sedentary</option>
              <option value="lightly_active">Lightly active</option>
              <option value="moderately_active">Moderately active</option>
              <option value="very_active">Very active</option>
              <option value="extra_active">Extra active</option>
            </Select>
          </div>
          <div>
            <Label htmlFor="goal">Goal</Label>
            <Select id="goal" value={form.goal} onChange={(e) => set("goal", e.target.value)}>
              <option value="">Select</option>
              <option value="weight_loss">Weight Loss</option>
              <option value="maintain">Maintain Weight</option>
              <option value="weight_gain">Weight Gain</option>
              <option value="general_fitness">General Fitness</option>
            </Select>
          </div>
        </div>
        {error ? <p className="text-sm text-clay">{error}</p> : null}
        {message ? <p className="text-sm text-leaf">{message}</p> : null}
        <Button type="submit" disabled={busy}>
          {busy ? "Saving..." : "Save profile"}
        </Button>
      </form>

      <section className="rounded-[32px] border border-line bg-forest p-6 text-cream-soft">
        <p className="text-sm text-cream/70">Estimated daily target</p>
        {user?.calorie_target ? (
          <>
            <p className="font-display mt-2 text-4xl">{user.calorie_target.calories} kcal</p>
            <p className="mt-3 text-sm text-cream/75">
              Protein {user.calorie_target.protein_g}g · Carbs {user.calorie_target.carbs_g}g · Fat {user.calorie_target.fat_g}g
            </p>
            <p className="mt-4 text-xs text-cream/60">
              Nutrition values are estimates and may vary based on ingredients, preparation, and portion size. Calorie
            targets are wellness estimates, not medical advice.
            </p>
          </>
        ) : (
          <p className="mt-3 text-cream/80">Add age, height, weight, activity, and goal to see an estimated target.</p>
        )}
      </section>
    </div>
  );
}
