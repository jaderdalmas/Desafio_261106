import pandas as pd


class TimelineService:

    @staticmethod
    def expand_hourly_market(m2: pd.DataFrame):

        expanded = m2.loc[m2.index.repeat(2)].reset_index(drop=True)
        expanded["timestamp"] = pd.to_datetime(expanded["timestamp"]) + pd.to_timedelta(
            expanded.index % 2 * 30,
            unit="minutes",
        )

        return expanded

    @staticmethod
    def align_hourly_market(
        half_hourly_market: pd.DataFrame,
        expanded_hourly_market: pd.DataFrame,
    ) -> pd.DataFrame:
        if len(half_hourly_market) != len(expanded_hourly_market):
            raise ValueError(
                "half-hourly and expanded hourly markets have different lengths"
            )

        half_hourly_dates = pd.to_datetime(
            half_hourly_market["timestamp"]
        ).dt.normalize()
        hourly_dates = pd.to_datetime(
            expanded_hourly_market["timestamp"]
        ).dt.normalize()
        if not half_hourly_dates.reset_index(drop=True).equals(
            hourly_dates.reset_index(drop=True)
        ):
            raise ValueError("market data does not cover the same calendar dates")

        aligned = expanded_hourly_market.copy()
        aligned["timestamp"] = half_hourly_market["timestamp"].to_numpy()
        return aligned
