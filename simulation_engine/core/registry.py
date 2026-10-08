"""Model registry. Only registered models can be executed."""

from __future__ import annotations

from simulation_engine.core.base import SimulationModel


class SimulationRegistry:
    def __init__(self) -> None:
        self._models: dict[str, SimulationModel] = {}

    def register(self, model: SimulationModel) -> None:
        if model.name in self._models:
            raise ValueError(f"Duplicate model name: {model.name}")
        self._models[model.name] = model

    def get(self, name: str) -> SimulationModel:
        try:
            return self._models[name]
        except KeyError as exc:
            known = ", ".join(sorted(self._models)) or "(none)"
            raise KeyError(f"Unknown model '{name}'. Registered models: {known}") from exc

    def names(self) -> list[str]:
        return sorted(self._models)

    def metadata(self) -> list[dict]:
        return [self._models[name].get_metadata() for name in self.names()]


def build_default_registry() -> SimulationRegistry:
    from simulation_engine.biosignals.ecg import SyntheticECG
    from simulation_engine.disease.diabetes_states import GlucoseStateModel
    from simulation_engine.epidemiology.sir import SIRModel, SEIRModel
    from simulation_engine.pharmacology.pk_one_compartment import (
        OneCompartmentIV,
        OneCompartmentOral,
    )
    from simulation_engine.pharmacology.pk_two_compartment import TwoCompartmentIV
    from simulation_engine.pharmacology.pkpd import IndirectGlucosePD
    from simulation_engine.physiology.cardiovascular import CardiovascularModel
    from simulation_engine.physiology.exponential import ExponentialDecay
    from simulation_engine.physiology.metabolic import GlucoseInsulinModel
    from simulation_engine.physiology.respiratory import RespiratoryModel

    registry = SimulationRegistry()
    for model in (
        ExponentialDecay(),
        OneCompartmentIV(),
        OneCompartmentOral(),
        TwoCompartmentIV(),
        IndirectGlucosePD(),
        GlucoseInsulinModel(),
        CardiovascularModel(),
        RespiratoryModel(),
        GlucoseStateModel(),
        SyntheticECG(),
        SIRModel(),
        SEIRModel(),
    ):
        registry.register(model)
    return registry


EXTENSION_POINTS = [
    {
        "id": "drug_discovery",
        "name": "Drug discovery lab",
        "phase": 10,
        "implemented": False,
        "status": "DEMO / PLACEHOLDER",
        "reason": (
            "No molecular-descriptor, affinity, ADME, or toxicity model is implemented. "
            "AEON 7080 will not invent binding scores."
        ),
    },
    {
        "id": "genomics",
        "name": "Genomics lab",
        "phase": 11,
        "implemented": False,
        "status": "DEMO / PLACEHOLDER",
        "reason": (
            "Sequence design, variant interpretation, and genotype-phenotype prediction "
            "are not implemented."
        ),
    },
    {
        "id": "imaging",
        "name": "Medical imaging lab",
        "phase": 12,
        "implemented": False,
        "status": "DEMO / PLACEHOLDER",
        "reason": "No segmentation, classification, or diagnostic imaging model is implemented.",
    },
    {
        "id": "clinical_trials",
        "name": "Clinical trial simulator",
        "phase": 14,
        "implemented": False,
        "status": "DEMO / PLACEHOLDER",
        "reason": "No synthetic-trial statistics engine is implemented in this build.",
    },
    {
        "id": "nutrition",
        "name": "Nutrition lab",
        "phase": None,
        "implemented": False,
        "status": "DEMO / PLACEHOLDER",
        "reason": "No nutrition model is implemented.",
    },
    {
        "id": "aging",
        "name": "Aging lab",
        "phase": None,
        "implemented": False,
        "status": "DEMO / PLACEHOLDER",
        "reason": "No aging model is implemented.",
    },
    {
        "id": "foundation_model",
        "name": "Scientific foundation-model training",
        "phase": 15,
        "implemented": False,
        "status": "DEMO / PLACEHOLDER",
        "reason": "LoRA, PEFT, and foundation-model fine-tuning are not implemented.",
    },
]
