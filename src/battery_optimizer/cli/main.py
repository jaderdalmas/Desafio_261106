import argparse
from pathlib import Path

import pandas as pd

from battery_optimizer.application.optimise_dispatch import (
    OptimiseDispatch,
)
from battery_optimizer.application.timeline_service import (
    TimelineService,
)
from battery_optimizer.infrastructure.excel_loader import (
    ExcelLoader,
)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description="Optimize battery dispatch.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/dispatch.csv"),
        help="CSV path for the optimized half-hourly schedule.",
    )
    args = parser.parse_args(argv)

    battery = ExcelLoader.load_battery("data/battery_parameters.xlsx")

    market1, market2 = ExcelLoader.load_markets("data/market_prices.xlsx")

    market2 = TimelineService.expand_hourly_market(market2)
    market2 = TimelineService.align_hourly_market(market1, market2)

    result = OptimiseDispatch(battery).execute(market1, market2)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(result["dispatch"]).to_csv(
        args.output,
        index=False,
        date_format="%Y-%m-%dT%H:%M:%S",
        float_format="%.10f",
    )
    print(f"Maximum profit: £{result['profit']:,.2f}")
    print(f"Dispatch intervals: {len(result['dispatch'])}")
    print(f"Dispatch saved to: {args.output}")


if __name__ == "__main__":
    main()
