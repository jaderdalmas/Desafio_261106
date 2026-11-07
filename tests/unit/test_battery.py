from battery_optimizer.domain.battery import (
    Battery,
)


def test_battery():

    battery = Battery(
        capacity_mwh=10,
        max_charge_mw=5,
        max_discharge_mw=5,
        initial_soc_mwh=5,
    )

    assert battery.capacity_mwh == 10
