import Link from "next/link";
import { notFound } from "next/navigation";
import Shell from "@/components/Shell";
import AssetChart from "@/components/AssetChart";
import { RegimeIcon, WORD } from "@/components/Glyphs";
import { assetTickers, loadAsset } from "@/lib/data";
import { FILL, NEG, POS } from "@/lib/theme";
import { big, dayMonth, pct, ratio, signed } from "@/lib/format";

export const dynamicParams = false;
export function generateStaticParams() { return assetTickers().map((ticker) => ({ ticker })); }

export default async function AssetPage({ params }: { params: Promise<{ ticker: string }> }) {
  const { ticker } = await params;
  const doc = loadAsset(ticker);
  if (!doc) notFound();
  const m = doc.model, f = doc.fundamentals, u = m.last_unusual_move;
  const readout = [
    { l: "Current regime", s: "Hidden Markov model, 3 states", v: m.regime },
    { l: "One-day loss limit, 95%", s: "Value-at-Risk, filtered historical", v: `−${m.var95_pct.toFixed(1)}%` },
    { l: "Expected swing, next 5 days", s: "GARCH(1,1), annualised", v: `${m.vol_forecast_5d_annualised_pct.toFixed(0)}%` },
    u ? { l: "Last unusual move", s: `${u.days_ago} days ago${u.z !== null ? `, ${Math.abs(u.z).toFixed(1)} standard deviations` : ""}`, v: u.direction }
      : { l: "Last unusual move", s: "none in this window", v: "None" },
  ];
  const funds = f ? [
    ["Revenue", big(f.revenue)], ["Net income", big(f.net_income)], ["Operating margin", pct(f.operating_margin)],
    ["Debt to equity", ratio(f.debt_to_equity)], ["Free cash flow", big(f.free_cash_flow)],
  ] : null;
  const others = assetTickers();
  return (
    <Shell sheet="asset" asOf={doc.as_of}>
      <section aria-label="Station report" style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "center", gap: "16px 32px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
          <RegimeIcon k={doc.regime.key} />
          <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <span className="eyebrow">Station · {doc.cls}{doc.stale ? " · stale data" : ""}</span>
            <h1 style={{ fontSize: 46 }}>{doc.ticker} <span style={{ fontWeight: 500, fontSize: 24, color: "var(--muted)" }}>{doc.name}</span></h1>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "baseline", gap: 18, flexWrap: "wrap" }}>
          <span className="mono" style={{ fontWeight: 500, fontSize: 40 }}>{doc.price.toLocaleString("en-US", { maximumFractionDigits: 2 })}</span>
          <span className="mono" style={{ fontWeight: 500, fontSize: 18, color: doc.change_1d >= 0 ? POS : NEG }}>{signed(doc.change_1d)}%</span>
          <span className="pill" style={{ background: FILL[doc.regime.key], fontSize: 13 }}>{WORD[doc.regime.key]} · {doc.regime.label.toLowerCase()}, day {doc.regime.days}</span>
        </div>
      </section>

      <nav aria-label="Choose a station" className="btns">
        {others.map((t) => <Link key={t} href={`/asset/${t}/`} className="btn mono" aria-current={t === doc.ticker ? "page" : undefined} style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", ...(t === doc.ticker ? { background: "var(--ink)", color: "var(--paper)" } : {}) }}>{t}</Link>)}
      </nav>

      <AssetChart doc={doc} var95={m.var95_pct} />

      <div className="flex">
        <section aria-label="Model readout" className="sec" style={{ flex: "1 1 440px" }}>
          <h2 style={{ margin: "0 0 6px" }}>Model readout</h2>
          {readout.map((k) => (
            <div className="kv" key={k.l}>
              <span style={{ display: "flex", flexDirection: "column" }}><span style={{ fontSize: 16, fontWeight: 500 }}>{k.l}</span><span className="muted" style={{ fontSize: 13 }}>{k.s}</span></span>
              <span className="mono" style={{ fontWeight: 500, fontSize: 22 }}>{k.v}</span>
            </div>
          ))}
        </section>
        <section aria-label="Fundamentals" className="sec" style={{ flex: "1 1 440px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 8, margin: "0 0 6px" }}>
            <h2>Fundamentals</h2>
            <span className="mono muted" style={{ fontSize: 12 }}>{f?.fiscal_year_end ? `year ended ${dayMonth(f.fiscal_year_end)} ${f.fiscal_year_end.slice(0, 4)}` : ""}</span>
          </div>
          {funds ? funds.map(([l, v]) => (
            <div className="kv" key={l}><span style={{ fontSize: 16, fontWeight: 500 }}>{l}</span><span className="mono" style={{ fontWeight: 500, fontSize: 18 }}>{v}</span></div>
          )) : <div className="kv"><span className="muted" style={{ fontSize: 15 }}>Fundamentals are not available for {doc.ticker}. Funds, currencies and crypto have none. For a stock, a failed fetch leaves this blank rather than guessing.</span></div>}
        </section>
      </div>
    </Shell>
  );
}
