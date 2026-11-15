import Shell from "@/components/Shell";
import RiskView from "@/components/RiskView";
import { assetTickers, loadRisk } from "@/lib/data";

export default function Risk() {
  const d = loadRisk();
  if (!d) return <Shell sheet="risk"><p className="lede">No risk data yet.</p></Shell>;
  const order = assetTickers().filter((t) => d.assets[t]);
  return (
    <Shell sheet="risk" asOf={d.as_of}>
      <section aria-label="Intro">
        <h1>Risk warnings</h1>
        <p className="lede">How bad a day could get, and whether the model&apos;s warning line held up when checked against what happened.</p>
      </section>
      <RiskView assets={d.assets} order={order} />
    </Shell>
  );
}
