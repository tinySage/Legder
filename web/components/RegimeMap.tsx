import type { ClassRegime } from "@/lib/types";
import { blob, contourCount } from "@/lib/geometry";
import { FILL } from "@/lib/theme";
import { Glyph, LABEL } from "./Glyphs";

const LAYOUT = [
  { cx: 230, cy: 215, R: 150, seed: 0.7 },
  { cx: 545, cy: 205, R: 140, seed: 2.1 },
  { cx: 835, cy: 225, R: 125, seed: 4.2 },
];

export default function RegimeMap({ classes }: { classes: ClassRegime[] }) {
  const summary = classes.map((c) => `${c.name} is ${LABEL[c.regime].toLowerCase()}`).join(", ");
  return (
    <svg role="img" aria-label={`Chart of three markets as weather regions. ${summary}.`} viewBox="0 0 1000 460">
      {classes.slice(0, 3).map((c, i) => {
        const L = LAYOUT[i];
        const n = contourCount(c.stress_probability);
        return (
          <g key={c.name}>
            <polygon points={blob(L.cx, L.cy, L.R, L.seed, 1)} fill={FILL[c.regime]} stroke="#2A2420" strokeWidth="2.5" strokeLinejoin="round" />
            {Array.from({ length: n }, (_, j) => (
              <polygon key={j} points={blob(L.cx, L.cy, L.R, L.seed, 1 - (j + 1) / (n + 1))} fill="none" stroke="#2A2420" strokeOpacity=".45" strokeWidth="1.3" strokeLinejoin="round" />
            ))}
            <g transform={`translate(${L.cx},${L.cy})`}><Glyph k={c.regime} /></g>
            <text x={L.cx} y={418} textAnchor="middle" fontFamily="Fraunces Variable, Georgia, serif" fontWeight={700} fontSize={23} fill="#2A2420">{c.name}</text>
            <text x={L.cx} y={440} textAnchor="middle" fontFamily="IBM Plex Mono, monospace" fontSize={13} fill="#2A2420">
              {`${LABEL[c.regime]} · day ${c.days} · ${Math.round(c.confidence * 100)}% sure`}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
