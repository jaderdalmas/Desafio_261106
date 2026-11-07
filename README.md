# Battery Arbitrage Platform

Battery dispatch optimization across multiple wholesale electricity markets.

## Features

- Multi-market optimization
- Linear Programming (PuLP)
- State-of-charge constraints
- Hourly and half-hourly market support
- FastAPI endpoint
- Docker support
- CI/CD pipelines
- Extensible solver abstraction

## Architecture

```text
Domain
Application
Infrastructure
Optimization
API
```

## Run

```bash
pip install -e .
python -m battery_optimizer.cli.main
```

The solver runs HiGHS with a single thread and a fixed seed. Hourly Market 2
commitments use one decision variable per hour instead of duplicated
half-hourly variables. The solver writes the dispatch to
`results/dispatch.csv`; use `--output path/to/file.csv` to choose another
location. Each solved dispatch interval is flushed to the result file as it is
written. If a run is interrupted during result writing, rerunning with the same
inputs and output path validates the saved rows and appends the remaining
intervals. Existing rows that do not match the newly computed schedule are
rejected rather than overwritten. The full-horizon optimization is recalculated
on rerun; saved rows let the CLI resume output writing, not the solver itself.
The CLI displays solver progress and limits optimization to 60 seconds by
default. If it finds a feasible schedule but cannot prove it optimal in that
time, it saves and reports the best feasible schedule. Use
`--time-limit seconds` to change the limit.

The CLI reads `data/battery_parameters.xlsx` and `data/market_prices.xlsx`.
The battery workbook supplies capacity, charge/discharge rates, and efficiency
losses. Since it does not specify an initial state of charge, the optimizer
starts at 50% of capacity. The market workbook must contain sheets named
`Half-hourly data` and `Hourly data`. Hourly prices are expanded to
half-hourly intervals before optimization. The optimization result includes the
maximum profit and a half-hourly dispatch schedule, with power attributed to
each market and the battery state of charge at both ends of each interval.

## Tests

```bash
pytest
```

## Future Improvements

- Degradation costs
- OR-Tools solver
- Gurobi solver
- Forecast-based optimization
- Multi-battery portfolios