import csv

import pandas as pd
import pytest

from battery_optimizer.cli.main import (
    _completed_dispatch_profit,
    _save_dispatch_resumable,
)


def test_dispatch_writer_appends_only_missing_rows(tmp_path):
    output = tmp_path / "dispatch.csv"
    dispatch = [
        {
            "timestamp": "2024-01-01T00:00:00",
            "charge_market1_mw": 1.0,
            "discharge_market1_mw": 0.0,
        },
        {
            "timestamp": "2024-01-01T00:30:00",
            "charge_market1_mw": 0.0,
            "discharge_market1_mw": 0.5,
        },
    ]

    _save_dispatch_resumable(output, dispatch[:1])
    _save_dispatch_resumable(output, dispatch)

    with output.open(newline="", encoding="utf-8") as file:
        rows = list(csv.reader(file))

    assert rows == [
        ["timestamp", "charge_market1_mw", "discharge_market1_mw"],
        ["2024-01-01T00:00:00", "1.0000000000", "0.0000000000"],
        ["2024-01-01T00:30:00", "0.0000000000", "0.5000000000"],
    ]


def test_dispatch_writer_rejects_a_mismatched_existing_result(tmp_path):
    output = tmp_path / "dispatch.csv"
    output.write_text(
        "timestamp,charge_market1_mw,discharge_market1_mw\n"
        "2024-01-01T00:00:00,9.0000000000,0.0000000000\n",
        encoding="utf-8",
    )
    dispatch = [
        {
            "timestamp": "2024-01-01T00:00:00",
            "charge_market1_mw": 1.0,
            "discharge_market1_mw": 0.0,
        }
    ]

    with pytest.raises(ValueError, match="differs at dispatch row 1"):
        _save_dispatch_resumable(output, dispatch)


def test_complete_dispatch_is_reused_without_reoptimizing(tmp_path):
    output = tmp_path / "dispatch.csv"
    dispatch = [
        {
            "timestamp": "2024-01-01T00:00:00",
            "charge_market1_mw": 1.0,
            "discharge_market1_mw": 0.0,
            "charge_market2_mw": 0.0,
            "discharge_market2_mw": 0.0,
            "soc_start_mwh": 2.0,
            "soc_end_mwh": 2.5,
            "profit_gbp": -5.0,
        },
        {
            "timestamp": "2024-01-01T00:30:00",
            "charge_market1_mw": 0.0,
            "discharge_market1_mw": 0.5,
            "charge_market2_mw": 0.0,
            "discharge_market2_mw": 0.0,
            "soc_start_mwh": 2.5,
            "soc_end_mwh": 2.0,
            "profit_gbp": 10.0,
        },
    ]
    _save_dispatch_resumable(output, dispatch)

    profit = _completed_dispatch_profit(
        output,
        pd.Series(pd.to_datetime([row["timestamp"] for row in dispatch])),
    )

    assert profit == pytest.approx(5.0)
