const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const API = {
  base: API_BASE_URL,
  chat: `${API_BASE_URL}/api/v1/chat`,
  chatHistory: (sessionId: string) => `${API_BASE_URL}/api/v1/chat/${sessionId}/history`,
  chatFeedback: `${API_BASE_URL}/api/v1/chat/feedback`,
  trends: (niche: string) => `${API_BASE_URL}/api/v1/trends/${encodeURIComponent(niche)}`,
  amazon: (niche: string) => `${API_BASE_URL}/api/v1/amazon/${encodeURIComponent(niche)}`,
  competitors: (product: string) => `${API_BASE_URL}/api/v1/competitors/${encodeURIComponent(product)}`,
  score: (product: string, niche?: string) => `${API_BASE_URL}/api/v1/score/${encodeURIComponent(product)}${niche ? `?niche=${encodeURIComponent(niche)}` : ""}`,
  report: (niche: string) => `${API_BASE_URL}/api/v1/report/${encodeURIComponent(niche)}`,
  salesSummary: (months?: number) => `${API_BASE_URL}/api/v1/sales/summary${months ? `?months=${months}` : ""}`,
  salesUpload: `${API_BASE_URL}/api/v1/sales/upload`,
  salesFiles: `${API_BASE_URL}/api/v1/sales/files`,
  researchHistory: `${API_BASE_URL}/api/v1/research/history`,
  niches: `${API_BASE_URL}/api/v1/niches`,
  analytics: `${API_BASE_URL}/api/v1/analytics`,
  health: `${API_BASE_URL}/api/v1/health`,
};

export interface Citation {
  id: number;
  source: string;
  section: string;
  page: number | null;
  relevance: number;
  text: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  category?: string | null;
  tool_used?: string | null;
  tool_result?: Record<string, unknown> | null;
  processing_time?: number;
  timestamp?: string;
}

export interface ChatResponse {
  session_id: string;
  message: string;
  answer: string;
  citations: Citation[];
  category: string | null;
  tool_used: string | null;
  tool_result: Record<string, unknown> | null;
  processing_time: number;
  timestamp: string;
}

export interface TrendData {
  niche: string;
  period: string;
  current_interest: number;
  trend_velocity: number;
  trend_direction: string;
  interest_over_time: { date: string; interest: number }[];
  rising_queries: { query: string; search_volume: number; growth_pct: number; trend: string }[];
  timestamp: string;
}

export interface AmazonProduct {
  asin: string;
  title: string;
  price: number;
  rating: number;
  review_count: number;
  bsr: number;
  bsr_category: string;
  estimated_monthly_sales: number;
  estimated_monthly_revenue: number;
  seller_count: number;
  fba_available: boolean;
  prime_eligible: boolean;
}

export interface Competitor {
  id: string;
  store_name: string;
  platform: string;
  price: number;
  rating: number;
  review_count: number;
  estimated_monthly_sales: number;
  shipping_speed: string;
  estimated_ad_spend: number | null;
  strengths: string[];
  weaknesses: string[];
}

export interface ProductScore {
  product: string;
  niche: string;
  composite_score: number;
  confidence: number;
  dimensions: Record<string, { score: number; weight: string }>;
  estimated_margin_pct: number;
  estimated_landed_cost: number;
  estimated_ad_cost_per_unit: number;
}

export interface SalesSummary {
  period: string;
  total_revenue: number;
  total_profit: number;
  total_ad_spend: number;
  overall_margin: number;
  roas: number;
  total_orders: number;
  top_products: { name: string; revenue: number; profit: number; quantity: number; orders: number }[];
  categories: { category: string; revenue: number; profit: number; quantity: number }[];
  stores: { store: string; revenue: number; profit: number }[];
}

export interface ResearchRecord {
  id: string;
  date_researched: string;
  product_name: string;
  niche: string;
  outcome: string;
  reason: string;
  margin_pct: number;
  months_active: number;
  revenue_total: number;
}

export interface Analytics {
  total_queries: number;
  queries_by_type: Record<string, number>;
  avg_response_time: number;
  feedback_positive: number;
  feedback_negative: number;
  files_uploaded: number;
  products_researched: number;
  reports_generated: number;
  satisfaction_rate: number;
  active_sessions: number;
  knowledge_chunks: number;
  sales_records: number;
  research_records: number;
}
