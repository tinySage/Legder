import type { RegimeKey } from "./types";

export const INK = "#2A2420", PAPER = "#F3EBDD", PANEL = "#EFE5D2", MUTED = "#6B5F54";
export const FILL: Record<RegimeKey, string> = { calm: "#BCD3D2", trend: "#E6C98E", stress: "#D9735B" };
export const CODE_KEY: Record<string, RegimeKey> = { c: "calm", t: "trend", S: "stress" };
export const POS = "#2F6B4F", NEG = "#A23B26", TOGETHER = "#6FA3A8";

/** Verdicts fall into three tiers; each tier has a fill and a mark so colour is never the only cue. */
export function tier(verdict: string): { fill: string; mark: string } {
  if (["Beats baseline", "Stable", "Pass"].includes(verdict)) return { fill: FILL.calm, mark: "✓" };
  if (verdict === "Mixed" || verdict === "Clustered") return { fill: FILL.trend, mark: "~" };
  return { fill: FILL.stress, mark: "!" };
}
