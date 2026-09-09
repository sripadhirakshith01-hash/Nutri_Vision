export function formatKcal(value: number | null | undefined) {
  if (value == null) return "—";
  return `${Math.round(value).toLocaleString()} kcal`;
}

export function formatGrams(value: number | null | undefined) {
  if (value == null) return "—";
  return `${Number(value).toFixed(value % 1 === 0 ? 0 : 1)} g`;
}

export function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

export function formatDay(iso: string) {
  const date = new Date(iso);
  const today = new Date();
  const yesterday = new Date();
  yesterday.setDate(today.getDate() - 1);
  if (date.toDateString() === today.toDateString()) return "Today";
  if (date.toDateString() === yesterday.toDateString()) return "Yesterday";
  return date.toLocaleDateString([], { weekday: "long", month: "short", day: "numeric" });
}

export function foodEmoji(food: string) {
  const map: Record<string, string> = {
    pizza: "🍕",
    hamburger: "🍔",
    tacos: "🌮",
    sushi: "🍣",
    ice_cream: "🍨",
    donuts: "🍩",
    french_fries: "🍟",
    hot_dog: "🌭",
    pancakes: "🥞",
    waffles: "🧇",
    omelette: "🥚",
    eggs_benedict: "🥚",
    breakfast_burrito: "🌯",
    ramen: "🍜",
    pho: "🍜",
    steak: "🥩",
    salad: "🥗",
    apple_pie: "🥧",
    chicken_wings: "🍗",
    fried_rice: "🍚",
    spaghetti_bolognese: "🍝",
    spaghetti_carbonara: "🍝",
    club_sandwich: "🥪",
    grilled_cheese_sandwich: "🥪",
  };
  if (map[food]) return map[food];
  if (food.includes("salad")) return "🥗";
  if (food.includes("cake") || food.includes("pie")) return "🍰";
  if (food.includes("soup")) return "🍲";
  return "🍽️";
}
