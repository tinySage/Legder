const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
export function fmtDate(iso: string): string {
  const [y, m, d] = iso.slice(0, 10).split("-").map(Number);
  return `${d} ${MONTHS[m - 1]} ${y}`;
}
export function fmtDateTime(iso: string): string {
  const t = iso.replace(" ", "T");
  return `${fmtDate(t)}, ${t.slice(11, 16)} UTC`;
}
export const monthOf = (iso: string) => MONTHS[Number(iso.slice(5, 7)) - 1];
export const dayMonth = (iso: string) => `${Number(iso.slice(8, 10))} ${monthOf(iso)}`;
export const minus = (n: number, digits = 1) => (n < 0 ? "−" : "") + Math.abs(n).toFixed(digits);
export const signed = (n: number, digits = 2) => (n >= 0 ? "+" : "−") + Math.abs(n).toFixed(digits);
export function big(n: number | null): string {
  if (n === null || n === undefined) return "not available";
  const a = Math.abs(n), s = n < 0 ? "−" : "";
  if (a >= 1e12) return `${s}$${(a / 1e12).toFixed(2)}T`;
  if (a >= 1e9) return `${s}$${(a / 1e9).toFixed(1)}B`;
  if (a >= 1e6) return `${s}$${(a / 1e6).toFixed(1)}M`;
  return `${s}$${a.toFixed(0)}`;
}
export const pct = (n: number | null, d = 1) => (n === null || n === undefined ? "not available" : `${(n * 100).toFixed(d)}%`);
export const ratio = (n: number | null) => (n === null || n === undefined ? "not available" : n.toFixed(2));
