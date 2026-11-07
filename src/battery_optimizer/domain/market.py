from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class MarketInterval:
    timestamp: datetime
    price: float