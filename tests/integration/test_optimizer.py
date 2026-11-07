import pandas as pd
import pytest

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
    market1 = pd.DataFrame({"timestamp": timestamps, "price": [100, 100]})
    market2 = pd.DataFrame({"timestamp": timestamps, "price": [0, 0]})

    result = PulpSolver(battery).solve(market1, market2)

    assert result["profit"] == pytest.approx(190)
    dispatch = result["dispatch"]
    assert len(dispatch) == 2
    assert dispatch[0]["discharge_market1_mw"] + dispatch[0][
        "discharge_market2_mw"
    ] == pytest.approx(2)
    assert dispatch[1]["soc_end_mwh"] == pytest.approx(0)


def test_optimizer_returns_reproducible_results():
    battery = Battery(
        capacity_mwh=4,
        max_charge_mw=2,
        max_discharge_mw=2,
        initial_soc_mwh=2,
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
    )
    timestamps = pd.date_range("2024-01-01", periods=4, freq="30min")
    market1 = pd.DataFrame({"timestamp": timestamps, "price": [10, 20, 100, 30]})
    market2 = pd.DataFrame({"timestamp": timestamps, "price": [15, 15, 25, 25]})
    solver = PulpSolver(battery)

    first = solver.solve(market1, market2)
    second = solver.solve(market1, market2)

    assert first["profit"] == pytest.approx(second["profit"])
    pd.testing.assert_frame_equal(
        pd.DataFrame(first["dispatch"]),
        pd.DataFrame(second["dispatch"]),
        check_exact=False,
        rtol=0,
        atol=1e-9,
    )


def test_optimizer_shares_power_and_energy_between_markets():
    battery = Battery(
        capacity_mwh=4,
        max_charge_mw=2,
        max_discharge_mw=2,
        initial_soc_mwh=2,
    )
    timestamps = pd.date_range("2024-01-01", periods=2, freq="30min")
    market1 = pd.DataFrame({"timestamp": timestamps, "price": [50, 20]})
    market2 = pd.DataFrame({"timestamp": timestamps, "price": [40, 40]})

    result = PulpSolver(battery).solve(market1, market2)
    dispatch = result["dispatch"]

    assert dispatch[0]["discharge_market2_mw"] == pytest.approx(
        dispatch[1]["discharge_market2_mw"]
    )
    for interval in dispatch:
        assert (
            interval["charge_market1_mw"] + interval["charge_market2_mw"]
            <= battery.max_charge_mw
        )
        assert (
            interval["discharge_market1_mw"] + interval["discharge_market2_mw"]
            <= battery.max_discharge_mw
        )
        assert not (
            interval["charge_market1_mw"] + interval["charge_market2_mw"] > 1e-6
            and interval["discharge_market1_mw"] + interval["discharge_market2_mw"]
            > 1e-6
        )
        assert 0 <= interval["soc_end_mwh"] <= battery.capacity_mwh


def test_optimizer_rejects_misaligned_market_data():
    timestamps = pd.date_range("2024-01-01", periods=2, freq="30min")
    market1 = pd.DataFrame({"timestamp": timestamps, "price": [10, 20]})
    market2 = pd.DataFrame(
        {"timestamp": timestamps + pd.Timedelta(minutes=1), "price": [5, 5]}
    )

    with pytest.raises(ValueError, match="timestamps must be aligned"):
        PulpSolver(Battery(4, 2, 2, 2)).solve(market1, market2)
