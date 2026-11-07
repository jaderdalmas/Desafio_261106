import pandas as pd
from pulp import *

from battery_optimizer.domain.battery import Battery


class PulpSolver:

    def __init__(
        self,
        battery: Battery,
    ):
        self.battery = battery

    def solve(
        self,
        market1: pd.DataFrame,
        market2: pd.DataFrame,
    ):

        horizon = len(market1)
        dt = 0.5

        model = LpProblem(
            "battery_dispatch",
            LpMaximize,
        )

        charge1 = {
            t: model.add_variable(f"charge1_{t}", lowBound=0)
            for t in range(horizon)
        }
        discharge1 = {
            t: model.add_variable(f"discharge1_{t}", lowBound=0)
            for t in range(horizon)
        }
        charge2 = {
            t: model.add_variable(f"charge2_{t}", lowBound=0)
            for t in range(horizon)
        }
        discharge2 = {
            t: model.add_variable(f"discharge2_{t}", lowBound=0)
            for t in range(horizon)
        }
        soc = {
            t: model.add_variable(
                f"soc_{t}",
                lowBound=0,
                upBound=self.battery.capacity_mwh,
            )
            for t in range(horizon + 1)
        }
        mode = {
            t: model.add_variable(f"mode_{t}", cat="Binary")
            for t in range(horizon)
        }

        model += (
            soc[0]
            == self.battery.initial_soc_mwh
        )

        profit = []

        for t in range(horizon):

            p1 = market1.iloc[t]["price"]
            p2 = market2.iloc[t]["price"]

            profit.append(
                dt
                * (
                    discharge1[t] * p1
                    + discharge2[t] * p2
                    - charge1[t] * p1
                    - charge2[t] * p2
                )
            )

            model += (
                charge1[t] + charge2[t]
                <= self.battery.max_charge_mw * mode[t]
            )

            model += (
                discharge1[t] + discharge2[t]
                <= self.battery.max_discharge_mw
                * (1 - mode[t])
            )

            model += (
                soc[t + 1]
                == soc[t]
                + dt * (
                    charge1[t]
                    + charge2[t]
                ) * self.battery.charge_efficiency
                - dt * (
                    discharge1[t]
                    + discharge2[t]
                ) / self.battery.discharge_efficiency
            )

        for h in range(0, horizon, 2):

            if h + 1 < horizon:
                model += charge2[h] == charge2[h + 1]
                model += discharge2[h] == discharge2[h + 1]

        model += lpSum(profit)

        model.solve()

        return {
            "profit": float(value(model.objective))
        }