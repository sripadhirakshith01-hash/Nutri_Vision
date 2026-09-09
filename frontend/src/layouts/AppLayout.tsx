import { Outlet } from "react-router-dom";
import { NavLink } from "react-router-dom";
import { Sidebar } from "../components/Sidebar";
import { useAuth } from "../hooks/useAuth";
import { APP_LINKS } from "../nav";
import { cn } from "../utils/cn";

export function AppLayout() {
  const { user, logout } = useAuth();
  const mobileLinks = APP_LINKS.filter((link) => link.to !== "/analytics");

  return (
    <div className="flex min-h-screen bg-cream">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex items-center justify-between border-b border-line/80 bg-cream/85 px-4 py-3 backdrop-blur-md md:px-8">
          <div className="md:hidden">
            <p className="font-display text-lg">NutriVision AI</p>
          </div>
          <p className="hidden text-sm text-stone md:block">See your food. Understand your nutrition.</p>
          <div className="flex items-center gap-4">
            <NavLink to="/profile" className="text-sm text-stone hover:text-ink">
              {user?.name}
            </NavLink>
            <button type="button" onClick={logout} className="text-sm text-forest hover:underline">
              Logout
            </button>
          </div>
        </header>
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 pb-24 md:px-8 md:py-8 md:pb-8">
          <Outlet />
        </main>
      </div>
      <nav className="fixed inset-x-0 bottom-0 z-30 border-t border-line bg-cream-soft/95 backdrop-blur md:hidden">
        <div className="grid grid-cols-5">
          {mobileLinks.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                cn("flex flex-col items-center gap-1 py-3 text-[11px]", isActive ? "text-forest" : "text-stone")
              }
            >
              <link.icon size={18} />
              {link.label === "NutriCoach" ? "Coach" : link.label}
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  );
}
