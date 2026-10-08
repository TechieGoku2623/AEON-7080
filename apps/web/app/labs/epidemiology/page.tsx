"use client";

import { ModelLab } from "@/components/simulation/model-lab";

export default function EpidemiologyPage() {
  return (
    <ModelLab
      model="sir"
      title="Abstract SIR"
      description="A closed, well-mixed compartment model. It is not a forecast and it is not tied to a named organism."
      seriesKey="infectious"
      defaults={{ beta_per_day: 0.5, gamma_per_day: 0.2, s0: 0.99, i0: 0.01, r0: 0 }}
    />
  );
}
