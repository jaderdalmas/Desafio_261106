from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class DispatchDecision:
    timestamp: datetime

    charge_market1_mw: float
    discharge_market1_mw: float

    charge_market2_mw: float
    discharge_market2_mw: float

    soc_mwh: float