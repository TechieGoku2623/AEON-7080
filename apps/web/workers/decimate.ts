/// <reference lib="webworker" />

self.onmessage = (event: MessageEvent<{ values: number[]; maxPoints: number }>) => {
  const { values, maxPoints } = event.data;
  const stride = Math.max(1, Math.ceil(values.length / Math.max(1, maxPoints)));
  const out: { i: number; v: number }[] = [];
  for (let i = 0; i < values.length; i += stride) out.push({ i, v: values[i] });
  self.postMessage(out);
};
