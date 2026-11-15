import test from "node:test";
import assert from "node:assert/strict";
import { contourCount, runs, sparkPoints, blob } from "../lib/geometry.ts";
import { tier } from "../lib/theme.ts";

test("contour count rises with stress probability", () => {
  assert.equal(contourCount(0), 2);
  assert.equal(contourCount(0.07), 2);
  assert.equal(contourCount(0.62), 6);
  assert.ok(contourCount(0.9) > contourCount(0.3));
});
test("runs groups consecutive codes", () => {
  assert.deepEqual(runs(["c", "c", "t", "S", "S"]), [{ start: 0, end: 2, code: "c" }, { start: 2, end: 3, code: "t" }, { start: 3, end: 5, code: "S" }]);
});
test("sparkline stays inside its box and handles flat series", () => {
  const p = sparkPoints([5, 5, 5, 5], 80, 24).split(" ").map((s) => s.split(",").map(Number));
  assert.ok(p.every(([x, y]) => x >= 0 && x <= 80 && y >= 0 && y <= 24));
});
test("blob is deterministic and closed-shaped", () => {
  assert.equal(blob(100, 100, 50, 1, 1), blob(100, 100, 50, 1, 1));
  assert.equal(blob(100, 100, 50, 1, 1).split(" ").length, 80);
});
test("verdict tiers carry a mark as well as a colour", () => {
  assert.equal(tier("Stable").mark, "✓");
  assert.equal(tier("Mixed").mark, "~");
  assert.equal(tier("Does not beat baseline").mark, "!");
  assert.equal(tier("Too many").mark, "!");
});
