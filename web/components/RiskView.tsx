"use client";
import { useState } from "react";
import { scaleLinear } from "d3-scale";
import { tier } from "@/lib/theme";
import type { RiskAsset } from "@/lib/types";

const N = (v: number, d = 1) => `−${Math.abs(v).toFixed(d)}%`;

export default function RiskView({ assets, order }: { assets: Record<string, RiskAsset>; order: string[] }) {
  const [t, setT] = useState(order.includes("SPY") ? "SPY" : order[0]);
  const a = assets[t], bt = a.backtest.fhs;
  const r = a.last120;
  const n = r.returns.length, K = 24, step = 900 / Math.max(1, n);
  const breaches = r.returns.filter((v, i) => v < r.limit[i]).length;
  const count = bt ? tier(bt.kupiec_p >= 0.05 ? "Pass" : "Too many") : null;
  const clust = bt ? tier(bt.independence_p >= 0.05 ? "Pass" : "Clustered") : null;
  const ext = Math.max(2, ...r.returns.map(Math.abs), ...r.limit.map(Math.abs));
  const k = 120 / ext;
  const dd = a.drawdown.series.slice(-252);
  const mn = Math.min(...dd, -0.1);
  const xd = scaleLinear().domain([0, dd.length - 1]).range([0, 400]);
  const dpts = ["0,10", ...dd.map((d, i) => `${xd(i).toFixed(1)},${(10 + (d / mn) * 160).toFixed(1)}`), "400,10"].join(" ");
  return (
    <>
      <nav aria-label="Choose a station" className="btns">
        {order.map((o) => <button key={o} className="btn mono" aria-pressed={o === t} onClick={() => setT(o)}>{o}</button>)}
      </nav>
      <section aria-label="Value-at-Risk backtest" className="sec" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "baseline", gap: 8 }}>
          <h2>{t}: did the 95% line hold?</h2>
          <span className="mono muted" style={{ fontSize: 13 }}>last {n} trading days</span>
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "12px 28px" }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: 12 }}>
            <span className="mono" style={{ fontWeight: 500, fontSize: 56, lineHeight: 1 }}>{breaches}</span>
            <span style={{ fontSize: 16, lineHeight: 1.3 }}>days past the line,<br />{Math.round(n * 0.05)} expected</span>
          </div>
          {bt && count && clust && <>
            <span className="pill" style={{ background: count.fill, fontSize: 13, padding: "4px 12px" }}>{count.mark} Count test: {bt.kupiec_p >= 0.05 ? "pass" : "too many or too few"}</span>
            <span className="pill" style={{ background: clust.fill, fontSize: 13, padding: "4px 12px" }}>{clust.mark} Clustering test: {bt.independence_p >= 0.05 ? "pass" : "breaches bunch up"}</span>
          </>}
        </div>
        <div className="frame"><div>
          <svg role="img" aria-label={`Daily returns as bars with the model's warning line; ${breaches} days went past the line`} viewBox="0 0 900 260">
            {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => <line key={`v${i}`} x1={i * 100} x2={i * 100} y1={0} y2={260} stroke="#2A2420" strokeOpacity=".14" />)}
            {[1, 2, 3, 4].map((j) => <line key={`h${j}`} x1={0} x2={900} y1={j * 52} y2={j * 52} stroke="#2A2420" strokeOpacity=".14" />)}
            <line x1={0} x2={900} y1={130} y2={130} stroke="#2A2420" strokeOpacity=".6" />
            {r.returns.map((v, i) => {
              const hit = v < r.limit[i], h = Math.max(2, Math.abs(v) * k);
              return <rect key={i} x={i * step} y={v >= 0 ? 130 - h : 130} width={Math.max(1, step - 1.9)} height={h} fill={hit ? "#D9735B" : "#BCD3D2"} stroke="#2A2420" strokeWidth=".8" />;
            })}
            <polyline points={r.limit.map((v, i) => `${(i * step + step / 2).toFixed(1)},${(130 - v * k).toFixed(1)}`).join(" ")} fill="none" stroke="#2A2420" strokeWidth="2.4" strokeDasharray="8 5" />
          </svg>
        </div></div>
        <div className="key">
          <span><i style={{ background: "#BCD3D2" }} />Daily return</span>
          <span><i style={{ background: "none", border: 0, borderTop: "2.4px dashed #2A2420", width: 26, height: 0 }} />Warning line (95% VaR)</span>
          <span><i style={{ background: "#D9735B" }} />Day past the line</span>
        </div>
        <p style={{ margin: 0, fontSize: 15, lineHeight: 1.55, maxWidth: 780 }}>
          A good 95% line is crossed about 1 day in 20, spread out evenly. Too many crossings means the model understates risk. Crossings that cluster mean it reacts too slowly to a change in mood.
          {bt && ` Over the longer ${bt.days}-day test, ${t} crossed the line ${bt.breaches} times against ${bt.expected.toFixed(0)} expected.`}
        </p>
      </section>
      <div className="flex">
        <section aria-label="Risk by asset" className="sec" style={{ flex: "1.2 1 480px" }}>
          <h2 style={{ margin: "0 0 8px" }}>By station</h2>
          <div className="risk-head"><span>Asset</span><span>1-day VaR</span><span>Tail loss</span><span>500-day test</span></div>
          {order.map((o) => { const x = assets[o], v = tier(x.verdict); return (
            <button key={o} onClick={() => setT(o)} className="risk-row" style={{ width: "100%", background: "none", border: 0, borderTop: "1px solid var(--rule)", textAlign: "left", cursor: "pointer", color: "inherit" }} aria-label={`Show ${o}`}>
              <span style={{ font: "600 16px var(--sans)" }}>{o}</span><span>{N(x.live.var95)}</span><span>{N(x.live.es95)}</span>
              <span><span className="pill" style={{ background: v.fill }}>{v.mark} {x.verdict}</span></span>
            </button>); })}
        </section>
        <section aria-label="Drawdown" className="sec" style={{ flex: "1 1 360px" }}>
          <h2 style={{ margin: "0 0 6px" }}>Drawdown, {t}</h2>
          <p className="muted" style={{ margin: "0 0 10px", fontSize: 15, lineHeight: 1.5 }}>How far the price sat below its previous high.</p>
          <div className="plate"><svg role="img" aria-label={`Drawdown from previous highs; deepest drop ${N(a.drawdown.max_drawdown_pct)}`} viewBox="0 0 400 180">
            <line x1={0} x2={400} y1={10} y2={10} stroke="#2A2420" strokeWidth="1.5" />
            <polygon points={dpts} fill="#D9735B" fillOpacity=".75" stroke="#2A2420" strokeWidth="2" strokeLinejoin="round" />
          </svg></div>
          <div className="axis" style={{ marginTop: 6 }}><span>12 months ago</span><span>Today</span></div>
          <div className="kv" style={{ marginTop: 12 }}><span style={{ fontSize: 16 }}>Deepest drop in the window</span><span className="mono" style={{ fontWeight: 500, fontSize: 22 }}>{N(a.drawdown.max_drawdown_pct)}</span></div>
        </section>
      </div>
    </>
  );
}
