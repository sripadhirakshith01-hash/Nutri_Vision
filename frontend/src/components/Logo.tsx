import { Link } from "react-router-dom";
import { cn } from "../utils/cn";

export function Logo({ compact = false, light = false }: { compact?: boolean; light?: boolean }) {
  return (
    <Link to="/" className="flex items-center gap-2.5">
      <span
        className={cn(
          "grid h-9 w-9 place-items-center rounded-2xl font-display text-lg",
          light ? "bg-cream-soft text-forest" : "bg-forest text-cream-soft",
        )}
      >
        N
      </span>
      {compact ? null : (
        <span>
          <span className={cn("block font-display text-lg leading-none", light ? "text-cream-soft" : "text-ink")}>
            NutriVision AI
          </span>
          <span className={cn("text-[11px]", light ? "text-cream/70" : "text-stone")}>See your food. Understand your nutrition.</span>
        </span>
      )}
    </Link>
  );
}
