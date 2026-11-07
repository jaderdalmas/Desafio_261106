import yaml

from battery_optimizer.domain.battery import (
    Battery,
)


def load_battery_config(path):

    with open(path) as f:
        config = yaml.safe_load(f)

    return Battery(**config)