from battery_optimizer.optimisation.pulp_solver import (
    PulpSolver,
)


class OptimiseDispatch:

    def __init__(self, battery):
        self.solver = PulpSolver(battery)

    def execute(
        self,
        market1,
        market2,
        *,
        time_limit: float | None = None,
        msg: bool = False,
    ):
        return self.solver.solve(
            market1,
            market2,
            time_limit=time_limit,
            msg=msg,
        )
