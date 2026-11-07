from dataclasses import dataclass


@dataclass(slots=True)
class Battery:
    capacity_mwh: float
    max_charge_mw: float
    max_discharge_mw: float
    initial_soc_mwh: float
    charge_efficiency: float = 1.0
    discharge_efficiency: float = 1.0