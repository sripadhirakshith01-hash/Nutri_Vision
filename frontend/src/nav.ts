import { BarChart3, LayoutDashboard, MessageCircle, ScanLine, UserRound, UtensilsCrossed } from "lucide-react";

export const APP_LINKS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/analyze", label: "Analyze", icon: ScanLine },
  { to: "/meals", label: "Meals", icon: UtensilsCrossed },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/chat", label: "NutriCoach", icon: MessageCircle },
  { to: "/profile", label: "Profile", icon: UserRound },
];
