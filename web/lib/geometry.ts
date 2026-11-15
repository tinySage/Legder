/** Organic region outline: a circle pushed in and out by three sine waves. Same shape every build. */
export function blob(cx: number, cy: number, R: number, seed: number, k: number): string {
  const pts: string[] = [];
  for (let i = 0; i < 80; i++) {
    const a = (i / 80) * 2 * Math.PI;
    const r = R * k * (1 + 0.12 * Math.sin(3 * a + seed) + 0.08 * Math.sin(5 * a + 2 * seed) + 0.05 * Math.sin(7 * a + 3 * seed));
    pts.push(`${(cx + r * Math.cos(a)).toFixed(1)},${(cy + r * Math.sin(a) * 0.82).toFixed(1)}`);
  }
  return pts.join(" ");
}

/** More contour lines mean a steeper change toward stress. */
export const contourCount = (stressProbability: number) => Math.round(2 + stressProbability * 6);

export function runs(codes: string[]): { start: number; end: number; code: string }[] {
  const out: { start: number; end: number; code: string }[] = [];
  codes.forEach((c, i) => {
    const last = out[out.length - 1];
    if (last && last.code === c) last.end = i + 1; else out.push({ start: i, end: i + 1, code: c });
  });
  return out;
}

export function sparkPoints(a: number[], w: number, h: number): string {
  if (a.length < 2) return "";
  const mn = Math.min(...a), mx = Math.max(...a);
  return a.map((v, i) => `${((i / (a.length - 1)) * w).toFixed(1)},${(h - 3 - ((v - mn) / (mx - mn || 1)) * (h - 6)).toFixed(1)}`).join(" ");
}
