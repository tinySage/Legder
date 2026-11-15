import type { RegimeKey } from "@/lib/types";

/** Calm: open circle with a dot. Trending: dot with a wind barb. Stress: filled circle with a bolt. */
export function Glyph({ k }: { k: RegimeKey }) {
  if (k === "calm") return <g><circle r="15" fill="#F3EBDD" stroke="#2A2420" strokeWidth="3.5" /><circle r="3.5" fill="#2A2420" /></g>;
  if (k === "trend") return <g><circle r="6" fill="#2A2420" /><path d="M0,0 L30,-30 M30,-30 L40,-25 M22,-22 L32,-17" stroke="#2A2420" strokeWidth="3.5" fill="none" strokeLinecap="round" /></g>;
  return <g><circle r="19" fill="#2A2420" /><path d="M-3,-11 L6,-1 L0,1 L5,11 L-7,0 L-1,-2 Z" fill="#F3EBDD" /></g>;
}

export function RegimeIcon({ k, size = 64 }: { k: RegimeKey; size?: number }) {
  const fill = { calm: "#BCD3D2", trend: "#E6C98E", stress: "#D9735B" }[k];
  return (
    <svg aria-hidden="true" width={size} height={size} viewBox="-32 -32 64 64">
      <rect x="-30" y="-30" width="60" height="60" fill={fill} stroke="#2A2420" strokeWidth="2" />
      <g transform="scale(.8)"><Glyph k={k} /></g>
    </svg>
  );
}

export const WORD: Record<RegimeKey, string> = { calm: "Clear", trend: "Wind", stress: "Storm" };
export const LABEL: Record<RegimeKey, string> = { calm: "Calm", trend: "Trending", stress: "Stress" };
