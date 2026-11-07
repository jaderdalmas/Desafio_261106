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
python -m src.battery_optimizer.cli.main
```

## Tests

```bash
pytest
```

## Future Improvements

- Battery efficiency
- Degradation costs
- OR-Tools solver
- Gurobi solver
- Forecast-based optimization
- Multi-battery portfolios