import math

import pandas as pd
from pulp import (
    COIN_CMD,
    LpMaximize,
    LpProblem,
    LpStatus,
    lpSum,
    value,
)

from battery_optimizer.domain.battery import Battery


class PulpSolver:
    def __init__(self, battery: Battery):
        self.battery = battery

    def solve(
        self,
        market1: pd.DataFrame,
        market2: pd.DataFrame,
    ) -> dict[str, object]:
        prices1, prices2 = self._validated_prices(market1, market2)
        horizon = len(prices1)
        interval_hours = 0.5

        model = LpProblem("battery_dispatch", LpMaximize)
        charge1 = {
            t: model.add_variable(f"charge1_{t}", lowBound=0) for t in range(horizon)
        }
        discharge1 = {
            t: model.add_variable(f"discharge1_{t}", lowBound=0) for t in range(horizon)
        }
        charge2 = {
            t: model.add_variable(f"charge2_{t}", lowBound=0) for t in range(horizon)
        }
        discharge2 = {
            t: model.add_variable(f"discharge2_{t}", lowBound=0) for t in range(horizon)
        }
        state_of_charge = {
            t: model.add_variable(
                f"soc_{t}",
                lowBound=0,
                upBound=self.battery.capacity_mwh,
            )
            for t in range(horizon + 1)
        }
        is_charging = {
            t: model.add_variable(f"is_charging_{t}", cat="Binary")
            for t in range(horizon)
        }

        model += state_of_charge[0] == self.battery.initial_soc_mwh

        interval_profit = []
        for t in range(horizon):
            interval_profit.append(
                interval_hours
                * (
                    discharge1[t] * prices1[t]
                    + discharge2[t] * prices2[t]
                    - charge1[t] * prices1[t]
                    - charge2[t] * prices2[t]
                )
            )
            model += (
                charge1[t] + charge2[t] <= self.battery.max_charge_mw * is_charging[t]
            )
            model += discharge1[t] + discharge2[t] <= self.battery.max_discharge_mw * (
                1 - is_charging[t]
            )
            model += state_of_charge[t + 1] == (
                state_of_charge[t]
                + interval_hours
                * (charge1[t] + charge2[t])
                * self.battery.charge_efficiency
                - interval_hours
                * (discharge1[t] + discharge2[t])
                / self.battery.discharge_efficiency
            )

        # A Market 2 power commitment applies to both half-hour intervals.
        for t in range(0, horizon, 2):
            model += charge2[t] == charge2[t + 1]
            model += discharge2[t] == discharge2[t + 1]

        model += lpSum(interval_profit)
        model.solve(COIN_CMD(msg=False))

        status = LpStatus[model.status]
        if status != "Optimal":
            raise RuntimeError(f"battery dispatch optimization failed: {status}")

        dispatch = []
        for t in range(horizon):
            dispatch.append(
                {
                    "timestamp": market1.iloc[t]["timestamp"],
                    "charge_market1_mw": value(charge1[t]),
                    "discharge_market1_mw": value(discharge1[t]),
                    "charge_market2_mw": value(charge2[t]),
                    "discharge_market2_mw": value(discharge2[t]),
                    "soc_start_mwh": value(state_of_charge[t]),
                    "soc_end_mwh": value(state_of_charge[t + 1]),
                    "profit_gbp": value(interval_profit[t]),
                }
            )

        return {
            "profit": float(value(model.objective)),
            "dispatch": dispatch,
        }

    @staticmethod
    def _validated_prices(
        market1: pd.DataFrame,
        market2: pd.DataFrame,
    ) -> tuple[list[float], list[float]]:
        for name, market in (("Market 1", market1), ("Market 2", market2)):
            missing = {"timestamp", "price"}.difference(market.columns)
            if missing:
                raise ValueError(
                    f"{name} data is missing columns: {', '.join(sorted(missing))}"
                )
            if market.empty:
                raise ValueError(f"{name} data must not be empty")

        if len(market1) != len(market2):
            raise ValueError("market data must cover the same half-hour intervals")
        if len(market1) % 2:
            raise ValueError("market data must contain complete hourly intervals")
        timestamps1 = pd.to_datetime(market1["timestamp"])
        timestamps2 = pd.to_datetime(market2["timestamp"])
        if timestamps1.isna().any() or timestamps2.isna().any():
            raise ValueError("market timestamps must not be missing")
        if not timestamps1.reset_index(drop=True).equals(
            timestamps2.reset_index(drop=True)
        ):
            raise ValueError("market data timestamps must be aligned")

        prices = []
        for name, market in (("Market 1", market1), ("Market 2", market2)):
            numeric_prices = pd.to_numeric(market["price"], errors="raise")
            if (
                numeric_prices.isna().any()
                or not numeric_prices.map(math.isfinite).all()
            ):
                raise ValueError(f"{name} prices must be finite")
            prices.append(numeric_prices.astype(float).tolist())

        prices1, prices2 = prices
        if any(prices2[t] != prices2[t + 1] for t in range(0, len(prices2), 2)):
            raise ValueError(
                "Market 2 prices must remain constant across each hourly interval"
            )

        return prices1, prices2
