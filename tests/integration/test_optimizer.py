import pandas as pd

from battery_optimizer.domain.battery import Battery
from battery_optimizer.optimisation.pulp_solver import PulpSolver


def test_optimizer_solves_a_small_dispatch():
    battery = Battery(
        capacity_mwh=4,
        max_charge_mw=2,
        max_discharge_mw=2,
        initial_soc_mwh=2,
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
    )
    timestamps = pd.date_range("2024-01-01", periods=2, freq="30min")
    market1 = pd.DataFrame(
        {"timestamp": timestamps, "price": [100, 100]}
    )
    market2 = pd.DataFrame(
        {"timestamp": timestamps, "price": [0, 0]}
    )

    result = PulpSolver(battery).solve(market1, market2)

    assert result["profit"] == 190