import argparse
import csv
import math
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


def _format_dispatch_row(dispatch_row: dict[str, object]) -> list[str]:
    return [
        pd.Timestamp(value).strftime("%Y-%m-%dT%H:%M:%S")
        if field == "timestamp"
        else f"{float(value):.10f}"
        for field, value in dispatch_row.items()
    ]


def _completed_dispatch_profit(output: Path, timestamps: pd.Series) -> float | None:
    if not output.exists() or output.stat().st_size == 0:
        return None

    expected_fields = [
        "timestamp",
        "charge_market1_mw",
        "discharge_market1_mw",
        "charge_market2_mw",
        "discharge_market2_mw",
        "soc_start_mwh",
        "soc_end_mwh",
        "profit_gbp",
    ]
    profits = []
    with output.open("r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        if next(reader, None) != expected_fields:
            return None

        for index, row in enumerate(reader):
            if index >= len(timestamps):
                raise ValueError(f"existing result file has extra rows: {output}")
            if len(row) != len(expected_fields):
                raise ValueError(f"existing result file has an invalid row: {index + 1}")
            expected_timestamp = pd.Timestamp(timestamps.iloc[index]).strftime(
                "%Y-%m-%dT%H:%M:%S"
            )
            if row[0] != expected_timestamp:
                raise ValueError(
                    f"existing result file timestamp differs at row {index + 1}: "
                    f"{output}"
                )
            try:
                values = [float(value) for value in row[1:]]
            except ValueError as error:
                raise ValueError(
                    f"existing result file has a non-numeric value at row {index + 1}"
                ) from error
            if not all(math.isfinite(value) for value in values):
                raise ValueError(
                    f"existing result file has a non-finite value at row {index + 1}"
                )
            profits.append(values[-1])

    if len(profits) != len(timestamps):
        return None
    return sum(profits)


def _save_dispatch_resumable(output: Path, dispatch: list[dict[str, object]]) -> None:
    if not dispatch:
        raise ValueError("dispatch must not be empty")

    fields = list(dispatch[0])
    completed = 0
    has_header = output.exists() and output.stat().st_size > 0

    if has_header:
        with output.open("r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            header = next(reader, None)
            if header != fields:
                raise ValueError(
                    f"existing result file has an unexpected header: {output}"
                )

            for row in reader:
                if completed >= len(dispatch):
                    raise ValueError(f"existing result file has extra rows: {output}")
                if row != _format_dispatch_row(dispatch[completed]):
                    raise ValueError(
                        f"existing result file differs at dispatch row {completed + 1}: "
                        f"{output}"
                    )
                completed += 1

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, lineterminator="\n")
        if not has_header:
            writer.writerow(fields)
            file.flush()
        for dispatch_row in dispatch[completed:]:
            writer.writerow(_format_dispatch_row(dispatch_row))
            file.flush()


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description="Optimize battery dispatch.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/dispatch.csv"),
        help="CSV path for the optimized half-hourly schedule.",
    )
    parser.add_argument(
        "--time-limit",
        type=float,
        default=60,
        help=(
            "Maximum optimization time in seconds. Saves the best feasible "
            "schedule found if optimality is not proven (default: 60)."
        ),
    )
    args = parser.parse_args(argv)
    if args.time_limit <= 0:
        parser.error("--time-limit must be greater than zero")

    print("Loading battery and market data...", flush=True)
    battery = ExcelLoader.load_battery("data/battery_parameters.xlsx")

    market1, market2 = ExcelLoader.load_markets("data/market_prices.xlsx")

    market2 = TimelineService.expand_hourly_market(market2)
    market2 = TimelineService.align_hourly_market(market1, market2)

    existing_profit = _completed_dispatch_profit(args.output, market1["timestamp"])
    if existing_profit is not None:
        print(f"Dispatch already complete. Saved profit: GBP {existing_profit:,.2f}")
        print(f"Dispatch intervals: {len(market1)}")
        print(f"Dispatch saved to: {args.output}")
        return

    print(
        f"Optimizing {len(market1):,} dispatch intervals "
        f"(time limit: {args.time_limit:g}s)...",
        flush=True,
    )
    result = OptimiseDispatch(battery).execute(
        market1,
        market2,
        time_limit=args.time_limit,
        msg=True,
    )

    dispatch = result["dispatch"]
    _save_dispatch_resumable(args.output, dispatch)
    outcome = "Maximum profit" if result["optimal"] else "Best feasible profit"
    print(f"{outcome}: GBP {result['profit']:,.2f}")
    if not result["optimal"]:
        print("Optimality was not proven before the time limit.")
    print(f"Dispatch intervals: {len(dispatch)}")
    print(f"Dispatch saved to: {args.output}")


if __name__ == "__main__":
    main()
