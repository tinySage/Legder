import { runs } from "@/lib/geometry";
import { CODE_KEY, FILL } from "@/lib/theme";

/** Chance of stress, with the fitted regime shaded behind it. */
export default function Barograph({ codes, values }: { codes: string[]; values: number[] }) {
  const n = values.length;
  const x = (i: number) => (i / Math.max(1, n - 1)) * 1000;
  const trace = values.map((v, i) => `${x(i).toFixed(1)},${(190 - v * 170).toFixed(1)}`).join(" ");
  const stressDays = codes.filter((c) => c === "S").length;
  return (
    <svg role="img" aria-label={`Chance of stress for equities over ${n} days on recorder paper; ${stressDays} days were in stress`} viewBox="0 0 1000 200">
      {runs(codes).map((r, i) => (
        <rect key={i} x={x(r.start)} y={0} width={Math.max(1, x(r.end) - x(r.start))} height={200} fill={FILL[CODE_KEY[r.code]]} fillOpacity={0.75} />
      ))}
      {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((i) => <line key={`v${i}`} x1={i * 100} x2={i * 100} y1={0} y2={200} stroke="#2A2420" strokeOpacity=".18" />)}
      {[1, 2, 3, 4].map((j) => <line key={`h${j}`} x1={0} x2={1000} y1={j * 40} y2={j * 40} stroke="#2A2420" strokeOpacity=".18" />)}
      <polyline points={trace} fill="none" stroke="#2A2420" strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}
