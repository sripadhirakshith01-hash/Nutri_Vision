import { NavLink } from "react-router-dom";
import { APP_LINKS } from "../nav";
import { cn } from "../utils/cn";

export function Sidebar() {
  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r border-white/10 bg-forest px-4 py-6 text-cream-soft md:flex">
      <NavLink to="/dashboard" className="mb-8 flex items-center gap-2.5 px-2">
        <span className="grid h-10 w-10 place-items-center rounded-2xl bg-cream-soft font-display text-lg text-forest">N</span>
        <span>
          <span className="block font-display text-lg leading-none">NutriVision</span>
          <span className="text-[11px] text-cream/65">AI nutrition</span>
        </span>
      </NavLink>
      <nav className="flex flex-1 flex-col gap-1">
        {APP_LINKS.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-2xl px-3 py-2.5 text-sm transition",
                isActive ? "bg-white/12 text-cream-soft" : "text-cream/70 hover:bg-white/8 hover:text-cream-soft",
              )
            }
          >
            <link.icon size={18} />
            {link.label}
          </NavLink>
        ))}
      </nav>
      <p className="px-3 text-[11px] leading-relaxed text-cream/45">
        Nutrition values are estimates, not medical advice.
      </p>
    </aside>
  );
}
