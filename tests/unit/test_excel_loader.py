from pathlib import Path

from battery_optimizer.application.timeline_service import TimelineService
from battery_optimizer.infrastructure.excel_loader import ExcelLoader

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"


def test_load_battery_parameters_from_workbook():
    battery = ExcelLoader.load_battery(DATA / "battery_parameters.xlsx")

    assert battery.capacity_mwh == 4
    assert battery.max_charge_mw == 2
    assert battery.max_discharge_mw == 2
    assert battery.initial_soc_mwh == 2
    assert battery.charge_efficiency == 0.95
    assert battery.discharge_efficiency == 0.95


def test_load_and_align_market_workbook():
    market1, hourly_market = ExcelLoader.load_markets(DATA / "market_prices.xlsx")
    market2 = TimelineService.expand_hourly_market(hourly_market)
    market2 = TimelineService.align_hourly_market(market1, market2)

    assert len(market1) == 52_608
    assert len(hourly_market) == 26_304
    assert market1["timestamp"].equals(market2["timestamp"])
    assert market1["timestamp"].duplicated().any()
    assert market2.loc[0, "timestamp"] == market1.loc[0, "timestamp"]
    assert market2.loc[1, "timestamp"] == market1.loc[1, "timestamp"]
    assert market2.loc[0, "price"] == market2.loc[1, "price"]
