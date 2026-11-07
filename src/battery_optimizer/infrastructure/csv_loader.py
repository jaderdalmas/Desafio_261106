from pathlib import Path

import pandas as pd


class CsvLoader:

    @staticmethod
    def load(path: str | Path) -> pd.DataFrame:
        df = pd.read_csv(path)

        if "timestamp" not in df.columns:
            raise ValueError("missing timestamp column")

        if "price" not in df.columns:
            raise ValueError("missing price column")

        df["timestamp"] = pd.to_datetime(df["timestamp"])

        return df.sort_values("timestamp")
