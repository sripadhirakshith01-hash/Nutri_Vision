import { ArrowRight, Camera, LineChart, MessageCircle, ScanSearch, Sparkles, Utensils } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "../components/ui/button";
import { useAuth } from "../hooks/useAuth";

const steps = [
  { title: "Food image", text: "Snap or upload a meal photo from your phone or desktop." },
  { title: "AI recognition", text: "Your Food-101 model identifies the dish and a confidence score." },
  { title: "Nutrition analysis", text: "Macros come from the nutrition table, scaled to your serving." },
  { title: "Personalized insights", text: "Dashboard, history, and NutriCoach update from your log." },
];

const features = [
  {
    title: "AI food recognition",
    text: "The existing EfficientNetV2-B0 Food-101 model runs on the backend — we never retrain it for this app.",
    icon: ScanSearch,
  },
  {
    title: "Nutrition tracking",
    text: "Calories, protein, carbs, fat, and fiber are estimated from typical per-100g values times your portion.",
    icon: Utensils,
  },
  {
    title: "NutriCoach",
    text: "Ask how you are doing today, what to eat next, or whether protein is on track — using your logged data.",
    icon: MessageCircle,
  },
  {
    title: "Analytics",
    text: "Weekly calories, macro trends, and whether you are under, near, or over your estimated target.",
    icon: LineChart,
  },
];

export function HomePage() {
  const { user } = useAuth();
  const analyzeTo = user ? "/analyze" : "/register";

  return (
    <div>
      <section className="mx-auto grid max-w-6xl items-center gap-12 px-4 py-16 lg:grid-cols-[1.1fr_0.9fr] lg:py-24">
        <div className="fade-up">
          <p className="text-sm uppercase tracking-[0.22em] text-leaf">NutriVision AI</p>
          <h1 className="font-display mt-4 max-w-xl text-5xl leading-[1.05] text-ink md:text-6xl">
            See your food.
            <br />
            Understand your nutrition.
          </h1>
          <p className="mt-5 max-w-lg text-lg text-stone">
            AI-powered food recognition and personalized nutrition tracking in one place. Photograph a meal, confirm the
            portion, and watch your day update.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to={analyzeTo}>
              <Button size="lg">
                Analyze My Food
                <ArrowRight size={16} />
              </Button>
            </Link>
            <Link to={user ? "/dashboard" : "/register"}>
              <Button size="lg" variant="secondary">
                Get Started
              </Button>
            </Link>
          </div>
          <p className="mt-6 max-w-md text-xs text-stone">
            Nutrition values are estimates and may vary based on ingredients, preparation method, and portion size. Not
            medical advice.
          </p>
        </div>
        <div className="relative overflow-hidden rounded-[36px] border border-line bg-forest p-8 text-cream-soft shadow-sm">
          <div className="absolute -right-10 -top-10 h-40 w-40 rounded-full bg-leaf/35" />
          <Camera className="text-cream/80" />
          <h2 className="font-display mt-4 text-3xl">From photo to plate insight</h2>
          <ol className="relative mt-8 space-y-5">
            {steps.map((step, index) => (
              <li key={step.title} className="flex gap-4">
                <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-white/12 text-sm">
                  {index + 1}
                </span>
                <span>
                  <p className="font-medium">{step.title}</p>
                  <p className="mt-1 text-sm text-cream/70">{step.text}</p>
                </span>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="border-y border-line bg-cream-soft/70 py-16">
        <div className="mx-auto max-w-6xl px-4">
          <p className="text-sm uppercase tracking-[0.2em] text-leaf">How it works</p>
          <h2 className="font-display mt-2 text-4xl">Four steps. One daily log.</h2>
          <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {steps.map((step) => (
              <article key={step.title} className="rounded-3xl border border-line bg-cream p-5">
                <h3 className="font-medium">{step.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-stone">{step.text}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-16">
        <p className="text-sm uppercase tracking-[0.2em] text-leaf">Inside the product</p>
        <h2 className="font-display mt-2 text-4xl">Built around your existing model</h2>
        <div className="mt-8 grid gap-4 md:grid-cols-2">
          {features.map((feature) => (
            <article key={feature.title} className="rounded-[28px] border border-line bg-cream-soft p-6">
              <feature.icon className="text-leaf" size={22} />
              <h3 className="mt-4 text-xl font-medium">{feature.title}</h3>
              <p className="mt-2 text-stone">{feature.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="mx-auto mb-20 max-w-6xl px-4">
        <div className="flex flex-col items-start justify-between gap-6 rounded-[32px] bg-forest px-8 py-10 text-cream-soft md:flex-row md:items-center">
          <div>
            <p className="flex items-center gap-2 text-sm text-cream/70">
              <Sparkles size={16} /> NutriCoach is ready when you are
            </p>
            <h2 className="font-display mt-2 text-3xl">Start logging meals in minutes.</h2>
          </div>
          <Link to={user ? "/analyze" : "/register"}>
            <Button size="lg" variant="secondary">
              {user ? "Analyze a meal" : "Create a free account"}
            </Button>
          </Link>
        </div>
      </section>
    </div>
  );
}
