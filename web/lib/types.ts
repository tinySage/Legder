export type RegimeKey = "calm" | "trend" | "stress";

export interface Meta {
  synthetic: boolean;
  models_run_at: string;
  fetched_at: string | null;
  assets: Record<string, { status: "ok" | "stale"; last_ok: string | null }>;
  credits: string[];
}
export interface ClassRegime {
  name: string; regime: RegimeKey; label: string; days: number; confidence: number;
  stress_probability: number; stress60: number[]; avg_spell_days: number;
}
export interface Station { ticker: string; name: string; cls: string; price: number; change_1d: number; spark: number[]; stale: boolean }
export interface Advisory { ticker: string; date: string; message: string }
export interface Regimes {
  synthetic: boolean; as_of: string; classes: ClassRegime[];
  equities_history: { dates: string[]; codes: string[]; stress_probability: number[] };
  stations: Station[]; advisories: Advisory[];
}
export interface Fundamentals {
  fiscal_year_end: string | null; revenue: number | null; net_income: number | null;
  operating_margin: number | null; debt_to_equity: number | null; free_cash_flow: number | null;
}
export interface AssetDoc {
  ticker: string; name: string; cls: string; as_of: string; stale: boolean; price: number; change_1d: number;
  regime: { key: RegimeKey; label: string; days: number; confidence: number };
  window: { dates: string[]; close: number[]; codes: string[]; band_lo: number[]; band_hi: number[];
            marks: { date: string; z: number | null; direction: "up" | "down" }[] };
  model: { regime: string; var95_pct: number; vol_forecast_5d_annualised_pct: number;
           last_unusual_move: { date: string; days_ago: number; z: number | null; direction: string } | null };
  fundamentals: Fundamentals | null;
}
export interface Backtest { days: number; breaches: number; expected: number; rate: number; kupiec_p: number; independence_p: number; verdict: string }
export interface RiskAsset {
  live: { var95: number; es95: number; historical: number };
  backtest: { fhs: Backtest | null; historical: Backtest | null; normal: Backtest | null };
  verdict: string;
  last120: { dates: string[]; returns: number[]; limit: number[] };
  drawdown: { series: number[]; max_drawdown_pct: number };
}
export interface RiskDoc { synthetic: boolean; as_of: string; assets: Record<string, RiskAsset> }
export interface CalmStress {
  calm: number | null; stress: number | null; difference?: number; ci95?: [number, number];
  n_calm: number; n_stress: number; rises_in_stress?: boolean; verdict: string;
  matrices?: { calm: number[][]; stress: number[][] };
}
export interface CorrelationDoc {
  synthetic: boolean; tickers: string[]; default_window: number;
  matrices: Record<string, number[][]>; calm_vs_stress: CalmStress;
}
export interface ModelCard { name: string; verdict: string; what: string; test: string; result: string; limit: string }
export interface ReportDoc { synthetic: boolean; forecast_vs_baseline: { name: string; value: number }[]; models: ModelCard[] }
