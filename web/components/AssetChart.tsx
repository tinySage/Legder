"use client";
import { useState } from "react";
import { scaleLinear } from "d3-scale";
import { runs } from "@/lib/geometry";
import { CODE_KEY, FILL } from "@/lib/theme";
import { dayMonth, monthOf } from "@/lib/format";
import type { AssetDoc } from "@/lib/types";

const RANGES = [["1M", 21], ["3M", 63], ["6M", 126], ["1Y", 252]] as const;
const W = 900, H = 340;

export default function AssetChart({ doc, var95 }: { doc: AssetDoc; var95: number }) {
  const [layers, setLayers] = useState({ regimes: true, band: true, adv: true, var: false });
  const [range, setRange] = useState<number>(126);
  const w = doc.window;
  const n = Math.min(range, w.close.length), s = w.close.length - n;
  const dates = w.dates.slice(s), close = w.close.slice(s), codes = w.codes.slice(s);
  const lo = w.band_lo.slice(s), hi = w.band_hi.slice(s);
  const varLevel = close[close.length - 1] * (1 - var95 / 100);
  const all = [...close, ...(layers.band ? [...lo, ...hi] : []), ...(layers.var ? [varLevel] : [])];
  const y = scaleLinear().domain([Math.min(...all) * 0.995, Math.max(...all) * 1.005]).range([H - 20, 20]);
  const X = (i: number) => (i / Math.max(1, n - 1)) * W;
  const line = close.map((v, i) => `${X(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
  const band = [...hi.map((v, i) => `${X(i).toFixed(1)},${y(v).toFixed(1)}`), ...lo.map((v, i) => [X(i), y(v)] as const).reverse().map(([a, b]) => `${a.toFixed(1)},${b.toFixed(1)}`)].join(" ");
  const marks = w.marks.map((m) => ({ m, i: dates.indexOf(m.date) })).filter((o) => o.i >= 0);
  const ticks: { i: number; label: string }[] = [];
  dates.forEach((d, i) => { if (i === 0 || d.slice(5, 7) !== dates[i - 1].slice(5, 7)) ticks.push({ i, label: monthOf(d) }); });
  const toggle = (k: keyof typeof layers) => setLayers((l) => ({ ...l, [k]: !l[k] }));
  const LAY: [keyof typeof layers, string][] = [["regimes", "Regimes"], ["band", "Volatility band"], ["adv", "Advisories"], ["var", "VaR level"]];

  return (
    <section aria-label="Price barograph" style={{ display: "flex", flexDirection: "column", gap: 12 }} className="sec">
      <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", gap: 12 }}>
        <div className="btns" role="group" aria-label="Layers">
          {LAY.map(([k, t]) => <button key={k} className="btn" aria-pressed={layers[k]} onClick={() => toggle(k)}>{t}</button>)}
        </div>
        <div className="seg" role="group" aria-label="Range">
          {RANGES.map(([t, v]) => <button key={t} className="btn mono" aria-pressed={range === v} onClick={() => setRange(v)}>{t}</button>)}
        </div>
      </div>
      <div className="frame"><div>
        <svg role="img" aria-label={`${doc.ticker} price over ${dates.length} trading days with regime shading, a volatility band and ${marks.length} advisories marked`} viewBox={`0 0 ${W} ${H}`}>
          {layers.regimes && runs(codes).map((r, i) => (
            <rect key={i} x={X(r.start)} y={0} width={Math.max(1, X(r.end - 1) - X(r.start) + W / n)} height={H} fill={FILL[CODE_KEY[r.code]]} fillOpacity={0.7} />
          ))}
          {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => <line key={`v${i}`} x1={i * 100} x2={i * 100} y1={0} y2={H} stroke="#2A2420" strokeOpacity=".16" />)}
          {[1, 2, 3, 4, 5].map((j) => <line key={`h${j}`} x1={0} x2={W} y1={j * 56.7} y2={j * 56.7} stroke="#2A2420" strokeOpacity=".16" />)}
          {layers.band && <polygon points={band} fill="#2A2420" fillOpacity=".12" />}
          {layers.var && <line x1={0} x2={W} y1={y(varLevel)} y2={y(varLevel)} stroke="#2A2420" strokeWidth="2" strokeDasharray="8 5" />}
          <polyline points={line} fill="none" stroke="#2A2420" strokeWidth="2.8" strokeLinejoin="round" strokeLinecap="round" />
          {layers.adv && marks.map(({ m, i }) => {
            const x = X(i), yy = y(close[i]) - 16;
            return <polygon key={m.date} points={`${x},${yy - 13} ${x - 11},${yy + 8} ${x + 11},${yy + 8}`} fill="#E6C98E" stroke="#2A2420" strokeWidth="2.2" strokeLinejoin="round"><title>{`Unusual move ${dayMonth(m.date)}, ${m.direction}`}</title></polygon>;
          })}
        </svg>
      </div></div>
      <div className="axis">{ticks.map((t) => <span key={t.i}>{t.label}</span>)}</div>
      <div className="key">
        {(["calm", "trend", "stress"] as const).map((k) => <span key={k}><i style={{ background: FILL[k] }} />{{ calm: "Calm", trend: "Trending", stress: "Stress" }[k]}</span>)}
        <span><i style={{ background: "rgba(42,36,32,.12)" }} />Expected range</span>
        <span><svg aria-hidden="true" width="18" height="16" viewBox="0 0 26 24" style={{ verticalAlign: "middle", marginRight: 8 }}><path d="M13 2 L24 22 H2 Z" fill="#E6C98E" stroke="#2A2420" strokeWidth="2.5" strokeLinejoin="round" /></svg>Unusual move</span>
      </div>
    </section>
  );
}
