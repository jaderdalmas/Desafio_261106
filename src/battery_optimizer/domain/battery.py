from dataclasses import dataclass
from math import isfinite


@dataclass(slots=True)
class Battery:
    capacity_mwh: float
    max_charge_mw: float
    max_discharge_mw: float
    initial_soc_mwh: float
    charge_efficiency: float = 1.0
    discharge_efficiency: float = 1.0

    def __post_init__(self):
        values = {
            "capacity_mwh": self.capacity_mwh,
            "max_charge_mw": self.max_charge_mw,
            "max_discharge_mw": self.max_discharge_mw,
            "initial_soc_mwh": self.initial_soc_mwh,
            "charge_efficiency": self.charge_efficiency,
            "discharge_efficiency": self.discharge_efficiency,
        }
        for name, value in values.items():
            if not isfinite(value):
                raise ValueError(f"{name} must be finite")

        for name in ("capacity_mwh", "max_charge_mw", "max_discharge_mw"):
            if values[name] <= 0:
                raise ValueError(f"{name} must be positive")

        if not 0 <= self.initial_soc_mwh <= self.capacity_mwh:
            raise ValueError("initial_soc_mwh must be within battery capacity")

        for name in ("charge_efficiency", "discharge_efficiency"):
            if not 0 < values[name] <= 1:
                raise ValueError(f"{name} must be in (0, 1]")
