import fs from "node:fs";
import path from "node:path";
import type { AssetDoc, CorrelationDoc, Meta, Regimes, ReportDoc, RiskDoc } from "./types";

const DIR = path.join(process.cwd(), "public", "data");

function read<T>(file: string): T | null {
  try { return JSON.parse(fs.readFileSync(path.join(DIR, file), "utf8")) as T; } catch { return null; }
}

export const loadMeta = () => read<Meta>("meta.json");
export const loadRegimes = () => read<Regimes>("regimes.json");
export const loadRisk = () => read<RiskDoc>("risk.json");
export const loadCorrelation = () => read<CorrelationDoc>("correlation.json");
export const loadReport = () => read<ReportDoc>("report.json");
export const loadAsset = (t: string) => read<AssetDoc>(`assets/${t}.json`);

export function assetTickers(): string[] {
  try {
    return fs.readdirSync(path.join(DIR, "assets")).filter((f) => f.endsWith(".json")).map((f) => f.replace(".json", "")).sort();
  } catch { return []; }
}
export const defaultAsset = () => { const t = assetTickers(); return t.includes("SPY") ? "SPY" : t[0] ?? "SPY"; };
