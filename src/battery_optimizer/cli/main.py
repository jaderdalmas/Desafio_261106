from battery_optimizer.application.optimise_dispatch import (
    OptimiseDispatch,
)
from battery_optimizer.application.timeline_service import (
    TimelineService,
)
from battery_optimizer.infrastructure.excel_loader import (
    ExcelLoader,
)


def main():

    battery = ExcelLoader.load_battery("data/battery_parameters.xlsx")

    market1, market2 = ExcelLoader.load_markets("data/market_prices.xlsx")

    market2 = TimelineService.expand_hourly_market(market2)
    market2 = TimelineService.align_hourly_market(market1, market2)

    result = OptimiseDispatch(battery).execute(market1, market2)

    print(f"Maximum profit: £{result['profit']:,.2f}")
    print(f"Dispatch intervals: {len(result['dispatch'])}")


if __name__ == "__main__":
    main()
