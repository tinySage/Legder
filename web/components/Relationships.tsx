"use client";
import { useState } from "react";
import { FILL, TOGETHER } from "@/lib/theme";
import type { CorrelationDoc } from "@/lib/types";

const GROUP: Record<string, string> = { SPY: TOGETHER, QQQ: TOGETHER, AAPL: TOGETHER, XOM: TOGETHER, GLD: FILL.trend, TLT: FILL.calm, BTC: FILL.stress, ETH: FILL.stress };
const mn = (v: number) => v.toFixed(2).replace("-", "−");

export default function Relationships({ doc }: { doc: CorrelationDoc }) {
  const wins = Object.keys(doc.matrices).map(Number).sort((a, b) => a - b);
  const [wi, setWi] = useState(Math.max(0, wins.indexOf(doc.default_window)));
  const [stressOnly, setStressOnly] = useState(false);
  const cs = doc.calm_vs_stress, T = doc.tickers;
  const stressM = cs.matrices?.stress;
  const useStress = stressOnly && !!stressM;
  const M = useStress ? stressM! : doc.matrices[String(wins[wi])];
  const title = useStress ? "Correlation, stress days only" : `Correlation, ${wins[wi]}-day window`;
  const P = T.map((t, i) => { const a = -Math.PI / 2 + (i * 2 * Math.PI) / T.length; return { t, x: 210 + 150 * Math.cos(a), y: 210 + 150 * Math.sin(a) }; });
  const edges = [];
  for (let i = 0; i < T.length; i++) for (let j = i + 1; j < T.length; j++) {
    const v = M[i][j];
    if (v > 0.4 || v < -0.2) edges.push({ i, j, v });
  }
  const cell = (v: number, same: boolean) => same ? "#2A2420" : v >= 0 ? `rgba(111,163,168,${(0.1 + v * 0.9).toFixed(2)})` : `rgba(217,115,91,${Math.min(1, 0.15 + -v * 2).toFixed(2)})`;
  return (
    <>
      <section aria-label="Controls" style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "flex-end", gap: "16px 40px" }}>
        <div style={{ maxWidth: 620 }}>
          <h1>Fronts</h1>
          <p className="lede">Which assets move together, and whether that changes when markets fall.</p>
        </div>
        <div style={{ flex: "1 1 420px", maxWidth: 560, display: "flex", flexWrap: "wrap", alignItems: "center", gap: "10px 20px" }}>
          <label htmlFor="win" style={{ display: "flex", alignItems: "center", gap: 14, fontSize: 15, flex: "1 1 300px", fontWeight: 500, opacity: useStress ? 0.45 : 1 }}>Window
            <input id="win" type="range" min={0} max={wins.length - 1} step={1} value={wi} disabled={useStress} onChange={(e) => setWi(Number(e.target.value))} style={{ flex: "1 1 140px", minHeight: 44, accentColor: "#2A2420" }} aria-valuetext={`${wins[wi]} days`} />
            <span className="mono" style={{ minWidth: 72, fontWeight: 500 }}>{wins[wi]} days</span>
          </label>
          <div className="seg" role="group" aria-label="Period">
            <button className="btn" aria-pressed={!stressOnly} onClick={() => setStressOnly(false)}>All days</button>
            <button className="btn" aria-pressed={stressOnly} onClick={() => setStressOnly(true)} disabled={!stressM}>Stress days</button>
          </div>
        </div>
      </section>
      <div className="flex">
        <section aria-label="Correlation matrix" className="sec" style={{ flex: "1 1 480px" }}>
          <h2 style={{ margin: "0 0 10px" }}>{title}</h2>
          <div role="table" aria-label="Correlation matrix" className="corr" style={{ gridTemplateColumns: `repeat(${T.length + 1}, minmax(0,1fr))` }}>
            <div role="columnheader" />
            {T.map((t) => <div role="columnheader" key={t} style={{ fontWeight: 600 }}>{t}</div>)}
            {T.map((a, i) => [
              <div role="rowheader" key={a} style={{ fontWeight: 600 }}>{a}</div>,
              ...T.map((b, j) => <div role="cell" key={a + b} style={{ background: cell(M[i][j], i === j) }}>{i === j ? "" : mn(M[i][j])}</div>),
            ])}
          </div>
          <div className="key" style={{ marginTop: 12 }}>
            <span><i style={{ background: "#D9735B" }} />Move opposite</span>
            <span><i style={{ background: "#EFE5D2" }} />Unrelated</span>
            <span><i style={{ background: TOGETHER }} />Move together</span>
          </div>
        </section>
        <section aria-label="Correlation network" className="sec" style={{ flex: "1 1 480px" }}>
          <h2 style={{ margin: "0 0 10px" }}>Network</h2>
          <div className="frame"><div>
            <svg role="img" aria-label={`Network of ${T.length} assets; ${edges.length} pairs are joined. Thicker lines move together more strongly, dashed lines move opposite`} viewBox="0 0 420 420">
              {[60, 110, 160, 200].map((r) => <circle key={r} cx={210} cy={210} r={r} fill="none" stroke="#2A2420" strokeOpacity=".18" />)}
              {edges.map(({ i, j, v }) => <line key={`${i}-${j}`} x1={P[i].x} y1={P[i].y} x2={P[j].x} y2={P[j].y} stroke="#2A2420" strokeWidth={Math.abs(v) * 6} strokeLinecap="round" strokeDasharray={v > 0 ? undefined : "7 6"} />)}
              {P.map((p) => (
                <g key={p.t}><circle cx={p.x} cy={p.y} r={26} fill={GROUP[p.t] ?? "#EFE5D2"} stroke="#2A2420" strokeWidth="2.5" />
                  <text x={p.x} y={p.y + 4} textAnchor="middle" fontFamily="IBM Plex Mono, monospace" fontWeight={500} fontSize={12} fill="#2A2420">{p.t}</text></g>
              ))}
            </svg>
          </div></div>
          <p className="muted" style={{ margin: "10px 0 0", fontSize: 14, lineHeight: 1.5 }}>Only pairs above 0.4 or below minus 0.2 are drawn. Dashed lines move opposite. Shading shows each asset&apos;s group.</p>
        </section>
      </div>
      <section aria-label="Calm versus stress" className="sec" style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "18px 48px" }}>
        <div style={{ flex: "1 1 320px", maxWidth: 520, display: "flex", flexDirection: "column", gap: 6 }}>
          <h2>Do correlations rise in a sell-off?</h2>
          <p style={{ margin: 0, fontSize: 15, lineHeight: 1.55 }}>Average correlation across all pairs, split by the regime model. The test runs on the data and its result is shown as found.</p>
          {cs.ci95 && <p className="muted" style={{ margin: 0, fontSize: 14 }}>Difference {mn(cs.difference ?? 0)}, 95% interval {mn(cs.ci95[0])} to {mn(cs.ci95[1])}. {cs.rises_in_stress ? "The interval sits above zero." : "The interval includes zero, so no rise is claimed."} Based on {cs.n_calm} calm and {cs.n_stress} stress days.</p>}
        </div>
        {cs.calm !== null && cs.stress !== null ? (
          <div style={{ display: "flex", gap: 44, flexWrap: "wrap" }}>
            <Stat label="Calm days" v={cs.calm} calm />
            <Stat label="Stress days" v={cs.stress} />
          </div>
        ) : <span className="muted">Not enough stress days to compare.</span>}
      </section>
    </>
  );
}

function Stat({ label, v, calm }: { label: string; v: number; calm?: boolean }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
      <svg aria-hidden="true" width="40" height="40" viewBox="-20 -20 40 40">
        {calm ? <><circle r="15" fill="#BCD3D2" stroke="#2A2420" strokeWidth="3" /><circle r="3.5" fill="#2A2420" /></>
          : <><circle r="18" fill="#2A2420" /><path d="M-3,-10 L5,-1 L0,1 L4,10 L-6,0 L-1,-2 Z" fill="#F3EBDD" /></>}
      </svg>
      <div style={{ display: "flex", flexDirection: "column" }}><span className="muted" style={{ fontSize: 13 }}>{label}</span><span className="mono" style={{ fontWeight: 500, fontSize: 34 }}>{mn(v)}</span></div>
    </div>
  );
}
