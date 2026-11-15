import Link from "next/link";
import Shell from "@/components/Shell";
import RegimeMap from "@/components/RegimeMap";
import Barograph from "@/components/Barograph";
import { LABEL, WORD } from "@/components/Glyphs";
import { loadRegimes } from "@/lib/data";
import { sparkPoints } from "@/lib/geometry";
import { FILL, NEG, POS } from "@/lib/theme";
import { dayMonth, signed } from "@/lib/format";
import type { ClassRegime } from "@/lib/types";

function bulletin(c: ClassRegime): string {
  const p = Math.round(c.stress_probability * 100);
  if (c.regime === "stress") return `In stress for ${c.days} ${c.days === 1 ? "day" : "days"}. Chance of stress today is ${p}%.`;
  if (c.regime === "trend") return `Trending for ${c.days} ${c.days === 1 ? "day" : "days"}. Chance of stress is ${p}%.`;
  return `Calm for ${c.days} ${c.days === 1 ? "day" : "days"}. Chance of stress is ${p}%.`;
}

export default function Home() {
  const d = loadRegimes();
  if (!d) return <Shell sheet="regimes"><p className="lede">No data yet. Run the pipeline first.</p></Shell>;
  const h = d.equities_history;
  const take = 120;
  const codes = h.codes.slice(-take), vals = h.stress_probability.slice(-take);
  return (
    <Shell sheet="regimes" asOf={d.as_of}>
      <section aria-label="Regime chart" className="flex">
        <div style={{ flex: "3 1 620px", display: "flex", flexDirection: "column", gap: 10 }}>
          <div className="frame"><div><RegimeMap classes={d.classes} /></div></div>
          <div className="key">
            <span className="eyebrow">Key</span>
            {(["calm", "trend", "stress"] as const).map((k) => <span key={k}><i style={{ background: FILL[k] }} />{LABEL[k]}</span>)}
            <span className="muted">More contour lines mean a higher chance of stress.</span>
          </div>
        </div>
        <aside style={{ flex: "1 1 280px", borderTop: "4px double var(--ink)" }}>
          <h2 style={{ margin: "14px 0 4px" }}>Bulletin</h2>
          {d.classes.map((c) => (
            <div className="row" key={c.name}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 8 }}>
                <span style={{ font: "700 18px var(--serif)" }}>{c.name}</span>
                <span className="pill" style={{ background: FILL[c.regime] }}>{WORD[c.regime]}</span>
              </div>
              <p style={{ margin: "6px 0 0", fontSize: 15, lineHeight: 1.5 }}>{bulletin(c)}</p>
            </div>
          ))}
        </aside>
      </section>

      <section aria-label="Equities barograph" className="sec" style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "baseline", gap: 8 }}>
          <h2>Equities barograph</h2>
          <span className="mono muted" style={{ fontSize: 13 }}>{vals.length} trading days · line is the chance of stress</span>
        </div>
        <div className="plate"><Barograph codes={codes} values={vals} /></div>
        <div className="axis"><span>{vals.length} days ago</span><span>Today</span></div>
      </section>

      <div className="flex">
        <section aria-label="Stations" className="sec stations" style={{ flex: "1 1 440px" }}>
          <h2 style={{ margin: "0 0 6px" }}>Stations</h2>
          {d.stations.map((s) => (
            <Link key={s.ticker} href={`/asset/${s.ticker}/`}>
              <span style={{ display: "flex", flexDirection: "column" }}>
                <span style={{ fontWeight: 600, fontSize: 16 }}>{s.ticker}</span>
                <span className="muted" style={{ fontSize: 13 }}>{s.name}{s.stale ? " · stale" : ""}</span>
              </span>
              <span className="mono" style={{ fontSize: 15 }}>{s.price.toLocaleString("en-US", { maximumFractionDigits: 2 })}</span>
              <span className="mono" style={{ fontWeight: 500, fontSize: 14, color: s.change_1d >= 0 ? POS : NEG }}>{signed(s.change_1d)}%</span>
              <svg aria-hidden="true" viewBox="0 0 80 24" width="80" height="24"><polyline points={sparkPoints(s.spark, 80, 24)} fill="none" stroke="#2A2420" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
            </Link>
          ))}
        </section>

        <section aria-label="Advisories" className="sec" style={{ flex: "1 1 440px" }}>
          <h2 style={{ margin: "0 0 6px" }}>Advisories</h2>
          {d.advisories.length === 0 && <div className="row"><p style={{ margin: 0, fontSize: 15 }}>No unusual moves flagged in the last 5 trading days.</p></div>}
          {d.advisories.map((a) => (
            <div className="row" key={a.ticker + a.date} style={{ display: "flex", gap: 14 }}>
              <svg aria-hidden="true" width="26" height="26" viewBox="0 0 26 26" style={{ flex: "none" }}>
                <path d="M13 3 L24 22 H2 Z" fill="#E6C98E" stroke="#2A2420" strokeWidth="2" strokeLinejoin="round" /><path d="M13 10 V16" stroke="#2A2420" strokeWidth="2.2" strokeLinecap="round" /><circle cx="13" cy="19" r="1.2" fill="#2A2420" />
              </svg>
              <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
                <div style={{ display: "flex", gap: 10, alignItems: "baseline" }}>
                  <Link href={`/asset/${a.ticker}/`} style={{ fontWeight: 600, fontSize: 16 }}>{a.ticker}</Link>
                  <span className="mono muted" style={{ fontSize: 12 }}>{dayMonth(a.date)}</span>
                </div>
                <span style={{ fontSize: 15, lineHeight: 1.5 }}>{a.message}</span>
              </div>
            </div>
          ))}
          <p style={{ margin: "6px 0 0", fontSize: 13, lineHeight: 1.5 }} className="muted">Advisories are logged. The report card shows what usually followed them.</p>
        </section>
      </div>
    </Shell>
  );
}
