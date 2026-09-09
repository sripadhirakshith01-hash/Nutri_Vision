export type CalorieTarget = {
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  method: string;
};

export type User = {
  user_id: number;
  name: string;
  email: string;
  age: number | null;
  gender: string | null;
  height: number | null;
  weight: number | null;
  activity_level: string | null;
  goal: string | null;
  calorie_target: CalorieTarget | null;
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
  user: User;
};

export type TopPrediction = {
  food: string;
  display_name: string;
  confidence: number;
};

export type NutritionValues = {
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  fiber_g?: number;
  calories: number;
  serving_size: number;
  basis: string;
};

export type PredictResponse = {
  prediction_id: number | null;
  food_name: string;
  display_name: string;
  confidence: number;
  low_confidence: boolean;
  top_predictions: TopPrediction[];
  nutrition_per_100g: NutritionValues | null;
  estimated: NutritionValues | null;
  estimated_grams: number | null;
  image_path: string | null;
  nutrition_missing: boolean;
  meal_type?: string | null;
};

export type PredictionItem = {
  prediction_id: number;
  id?: number;
  food_name: string;
  display_name: string;
  confidence: number;
  estimated_grams: number | null;
  estimated_calories: number | null;
  protein_g: number | null;
  carbs_g: number | null;
  fat_g: number | null;
  fiber_g?: number | null;
  image_path: string | null;
  predicted_at: string;
  category: string | null;
  meal_type?: string | null;
};

export type FoodItem = {
  id: number;
  food_name: string;
  display_name: string;
  protein_g: number | null;
  carbs_g: number | null;
  fat_g: number | null;
  fiber_g: number | null;
  calories: number | null;
  serving_size: number;
  category: string | null;
};

export type Insight = {
  icon: string;
  tone: string;
  text: string;
};

export type Recommendation = {
  title: string;
  text: string;
};

export type RemainingBudget = {
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
};

export type WeeklyPoint = {
  date: string;
  label?: string;
  calories: number;
  protein_g?: number;
  carbs_g?: number;
  fat_g?: number;
  status?: string | null;
};

export type DashboardData = {
  today: {
    calories: number;
    protein_g: number;
    carbs_g: number;
    fat_g: number;
    fiber_g?: number;
    meals: number;
  };
  targets: CalorieTarget | null;
  remaining: RemainingBudget | null;
  goal_status: "under_target" | "near_target" | "over_target" | null;
  today_meals: PredictionItem[];
  weekly_calories: WeeklyPoint[];
  macros: { protein_g: number; carbs_g: number; fat_g: number; fiber_g?: number };
  top_foods: { food: string; display_name: string; count: number; calories: number }[];
  meal_frequency: { category: string; count: number }[];
  insights: Insight[];
  recommendations: Recommendation[];
};

export type ChatMessage = {
  message_id?: number;
  role: "user" | "assistant";
  content: string;
  created_at?: string;
  conversation_id?: string | null;
};

export type ChatResponse = ChatMessage & {
  response: string;
  conversationId: string;
  food?: {
    food_name: string;
    display_name: string;
    confidence: number;
    nutrition_per_100g?: {
      calories: number;
      protein_g: number;
      carbs_g: number;
      fat_g: number;
      fiber_g?: number;
    } | null;
  } | null;
  provider?: string | null;
};
