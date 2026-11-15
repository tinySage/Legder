import type { ReactNode } from "react";
import Link from "next/link";
import { loadMeta, defaultAsset } from "@/lib/data";
import { fmtDate, fmtDateTime } from "@/lib/format";

const SHEETS = [
  { key: "regimes", label: "Regimes", href: "/" },
  { key: "asset", label: "Asset", href: `/asset/${defaultAsset()}/` },
  { key: "risk", label: "Risk", href: "/risk/" },
  { key: "relationships", label: "Relationships", href: "/relationships/" },
  { key: "report", label: "Report card", href: "/report/" },
];

export default function Shell({ sheet, asOf, children }: { sheet: string; asOf?: string; children: ReactNode }) {
  const meta = loadMeta();
  const idx = SHEETS.findIndex((s) => s.key === sheet) + 1;
  const stamp = sheet === "report" && meta
    ? `Models last re-run ${fmtDateTime(meta.models_run_at)}`
    : `${asOf ? fmtDate(asOf) + " close" : "No data"} · prices are delayed`;
  return (
    <div className="page">
      <header className="top">
        <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <span className="eyebrow">Daily market weather chart</span>
          <span className="brand">Ledger</span>
        </div>
        <div className="stamp">{stamp}<br /><span>Sheet {idx} of 5 · not advice</span></div>
      </header>
      <nav className="sheets" aria-label="Sheets">
        {SHEETS.map((s) => (
          <Link key={s.key} href={s.href} aria-current={s.key === sheet ? "page" : undefined}>{s.label}</Link>
        ))}
      </nav>
      {meta?.synthetic && (
        <div className="banner" role="note">
          Synthetic demo data. These numbers come from a simulated market, not real prices, and prove nothing about the models. Real data replaces them after the first scheduled refresh.
        </div>
      )}
      {children}
      <footer className="foot">
        <p style={{ margin: "0 0 6px" }}><strong>Educational tool, not financial advice. Data is delayed.</strong></p>
        <p style={{ margin: 0 }}>{(meta?.credits ?? []).join(" · ")}</p>
      </footer>
    </div>
  );
}
