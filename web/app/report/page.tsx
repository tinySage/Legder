import Shell from "@/components/Shell";
import { loadReport } from "@/lib/data";
import { FILL, tier } from "@/lib/theme";

export default function Report() {
  const d = loadReport();
  if (!d) return <Shell sheet="report"><p className="lede">No report yet.</p></Shell>;
  const mx = Math.max(1.3, ...d.forecast_vs_baseline.map((f) => f.value * 1.1));
  return (
    <Shell sheet="report">
      <section aria-label="Intro" style={{ maxWidth: 740 }}>
        <h1>Forecast verification</h1>
        <p className="lede">Weather services publish how often their forecasts were right. This sheet does the same. Every model is tested on data it has not seen, against a simple baseline, and the result is shown whether or not it flatters the model.</p>
      </section>
      <section aria-label="Forecast versus baseline" className="sec" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "baseline", gap: 8 }}>
          <h2>Do price forecasts beat &ldquo;tomorrow equals today&rdquo;?</h2>
          <span className="mono muted" style={{ fontSize: 13 }}>next-day error · walk-forward test{d.synthetic ? " · synthetic data" : ""}</span>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {d.forecast_vs_baseline.map((f, i) => (
            <div key={f.name} style={{ display: "grid", gridTemplateColumns: "minmax(130px,200px) 1fr 70px", alignItems: "center", gap: 14 }}>
              <span style={{ fontSize: 16, fontWeight: 500 }}>{f.name}</span>
              <div style={{ position: "relative", height: 26, border: "1px solid var(--ink)", background: "var(--panel)" }} role="img" aria-label={`${f.name} error ${f.value.toFixed(2)} relative to baseline 1.00`}>
                <div style={{ width: `${(f.value / mx) * 100}%`, height: "100%", background: i === 0 ? FILL.calm : f.value < 1 ? FILL.calm : FILL.trend, borderRight: "1px solid var(--ink)" }} />
                <div style={{ position: "absolute", left: `${(1 / mx) * 100}%`, top: -6, bottom: -6, borderLeft: "2px dashed var(--ink)" }} />
              </div>
              <span className="mono" style={{ fontWeight: 500, fontSize: 16, textAlign: "right" }}>{f.value.toFixed(2)}</span>
            </div>
          ))}
        </div>
        <p style={{ margin: 0, fontSize: 15, lineHeight: 1.55, maxWidth: 780 }}>Lower is better and the dashed line is the baseline. Gaps this small sit inside the noise, so a model is shown as an improvement only when a significance test says so. Daily prices are close to a random walk, and beating the naive guess is hard.</p>
      </section>
      <section aria-label="All models" className="sec">
        <h2 style={{ margin: "0 0 6px" }}>All models</h2>
        <div className="cards">
          {d.models.map((m) => { const t = tier(m.verdict); return (
            <article key={m.name} className="row" style={{ display: "flex", flexDirection: "column", gap: 10, padding: "18px 0 20px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 10 }}>
                <h3>{m.name}</h3><span className="pill" style={{ background: t.fill }}>{t.mark} {m.verdict}</span>
              </div>
              <p style={{ margin: 0, fontSize: 15, lineHeight: 1.5 }}>{m.what}</p>
              <div style={{ fontSize: 14, lineHeight: 1.55, paddingLeft: 12, borderLeft: "3px solid var(--ink)" }}>
                <span className="muted">Tested by</span> {m.test}<br /><span className="muted">Result</span> <strong style={{ fontWeight: 600 }}>{m.result}</strong>
              </div>
              <p className="muted" style={{ margin: 0, fontSize: 14, lineHeight: 1.5 }}><span style={{ color: "var(--ink)", fontWeight: 600 }}>Limitation</span> {m.limit}</p>
            </article>); })}
        </div>
      </section>
    </Shell>
  );
}
