from battery_optimizer.application.optimise_dispatch import (
    OptimiseDispatch,
)

from battery_optimizer.infrastructure.config_loader import (
    load_battery_config,
)

from battery_optimizer.infrastructure.csv_loader import (
    CsvLoader,
)

from battery_optimizer.application.timeline_service import (
    TimelineService,
)


def main():

    battery = load_battery_config(
        "configs/battery.yaml"
    )

    market1 = CsvLoader.load(
        "data/market1.csv"
    )

    market2 = CsvLoader.load(
        "data/market2.csv"
    )

    market2 = (
        TimelineService
        .expand_hourly_market(
            market2
        )
    )

    result = (
        OptimiseDispatch(battery)
        .execute(
            market1,
            market2,
        )
    )

    print(result)


if __name__ == "__main__":
    main()