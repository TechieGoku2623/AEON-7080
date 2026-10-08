export function decimate(values: number[], maxPoints: number): { i: number; v: number }[] {
  if (maxPoints < 1 || values.length === 0) return [];
  const stride = Math.max(1, Math.ceil(values.length / maxPoints));
  const out: { i: number; v: number }[] = [];
  for (let i = 0; i < values.length; i += stride) out.push({ i, v: values[i] });
  return out;
}
