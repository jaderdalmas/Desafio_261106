from math import isfinite
from pathlib import Path
from typing import ClassVar

import pandas as pd

from battery_optimizer.domain.battery import Battery


class ExcelLoader:
    BATTERY_PARAMETERS: ClassVar[dict[str, str]] = {
        "Max charging rate": "max_charge_mw",
        "Max discharging rate": "max_discharge_mw",
        "Max storage volume": "capacity_mwh",
        "Battery charging efficiency": "charge_loss",
        "Battery discharging efficiency": "discharge_loss",
    }

    @classmethod
    def load_battery(cls, path: str | Path) -> Battery:
        rows = pd.read_excel(
            path,
            sheet_name="Data",
            header=None,
            usecols="A:B",
            skiprows=1,
            names=["parameter", "value"],
        )
        values = {
            str(parameter).strip(): value
            for parameter, value in rows.itertuples(index=False, name=None)
            if pd.notna(parameter) and pd.notna(value)
        }

        missing = set(cls.BATTERY_PARAMETERS).difference(values)
        if missing:
            raise ValueError(
                f"battery workbook is missing parameters: {', '.join(sorted(missing))}"
            )

        parameters = {}
        for label, name in cls.BATTERY_PARAMETERS.items():
            try:
                value = float(values[label])
            except (TypeError, ValueError) as error:
                raise ValueError(
                    f"battery parameter {label!r} must be numeric"
                ) from error
            if not isfinite(value):
                raise ValueError(f"battery parameter {label!r} must be finite")
            parameters[name] = value

        for name in ("capacity_mwh", "max_charge_mw", "max_discharge_mw"):
            if parameters[name] <= 0:
                raise ValueError(f"battery parameter {name} must be positive")

        for name in ("charge_loss", "discharge_loss"):
            if not 0 <= parameters[name] < 1:
                raise ValueError(f"battery parameter {name} must be in [0, 1)")

        capacity = parameters["capacity_mwh"]
        return Battery(
            capacity_mwh=capacity,
            max_charge_mw=parameters["max_charge_mw"],
            max_discharge_mw=parameters["max_discharge_mw"],
            initial_soc_mwh=capacity / 2,
            charge_efficiency=1 - parameters["charge_loss"],
            discharge_efficiency=1 - parameters["discharge_loss"],
        )

    @staticmethod
    def load_markets(path: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
        return (
            ExcelLoader._load_market_sheet(path, "Half-hourly data"),
            ExcelLoader._load_market_sheet(path, "Hourly data"),
        )

    @staticmethod
    def _load_market_sheet(path: str | Path, sheet_name: str) -> pd.DataFrame:
        frame = pd.read_excel(path, sheet_name=sheet_name, usecols=[0, 1])
        if len(frame.columns) != 2:
            raise ValueError(f"market sheet {sheet_name!r} must have two columns")

        frame.columns = ["timestamp", "price"]
        frame = frame.dropna(how="all")
        if frame.empty:
            raise ValueError(f"market sheet {sheet_name!r} contains no data")
        if frame[["timestamp", "price"]].isna().any().any():
            raise ValueError(f"market sheet {sheet_name!r} contains incomplete rows")

        if pd.api.types.is_datetime64_any_dtype(frame["timestamp"]):
            frame["timestamp"] = pd.to_datetime(frame["timestamp"])
        else:
            numeric_timestamps = pd.to_numeric(frame["timestamp"], errors="coerce")
            if numeric_timestamps.notna().all():
                frame["timestamp"] = pd.to_datetime(
                    numeric_timestamps,
                    unit="D",
                    origin="1899-12-30",
                )
            elif numeric_timestamps.notna().any():
                raise ValueError(
                    f"market sheet {sheet_name!r} contains inconsistent timestamps"
                )
            else:
                frame["timestamp"] = pd.to_datetime(
                    frame["timestamp"],
                    errors="raise",
                )

        frame["timestamp"] = frame["timestamp"].dt.round("s")
        frame["price"] = pd.to_numeric(frame["price"], errors="raise")
        if frame["timestamp"].isna().any() or not frame["price"].map(isfinite).all():
            raise ValueError(f"market sheet {sheet_name!r} contains invalid data")

        return frame.reset_index(drop=True)
