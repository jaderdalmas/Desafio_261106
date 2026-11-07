import pandas as pd


class TimelineService:

    @staticmethod
    def expand_hourly_market(m2: pd.DataFrame):

        expanded = m2.loc[
            m2.index.repeat(2)
        ].reset_index(drop=True)

        return expanded