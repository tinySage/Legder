import Shell from "@/components/Shell";
import Relationships from "@/components/Relationships";
import { loadCorrelation, loadRegimes } from "@/lib/data";

export default function Page() {
  const d = loadCorrelation();
  return (
    <Shell sheet="relationships" asOf={loadRegimes()?.as_of}>
      {d ? <Relationships doc={d} /> : <p className="lede">No correlation data yet.</p>}
    </Shell>
  );
}
