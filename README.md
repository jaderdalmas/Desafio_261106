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