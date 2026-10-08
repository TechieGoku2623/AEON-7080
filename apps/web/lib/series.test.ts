import { describe, expect, it } from "vitest";
import { decimate } from "./series";

describe("decimate", () => {
  it("keeps the first sample and stays within the point budget", () => {
    const values = Array.from({ length: 100 }, (_, i) => i);
    const out = decimate(values, 10);
    expect(out[0]).toEqual({ i: 0, v: 0 });
    expect(out.length).toBeLessThanOrEqual(10);
    expect(out.at(-1)?.v).toBe(90);
  });
});
