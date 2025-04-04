"""Constants for the OneMeter Cloud integration."""
from datetime import timedelta

DOMAIN = "onemeter"

# Config flow
CONF_API_KEY = "api_key"

# Defaults
DEFAULT_NAME = "OneMeter"
SCAN_INTERVAL = timedelta(minutes=5)

# Sensor types
SENSOR_TYPES = {
    "energy": {
        "name": "Energy",
        "icon": "mdi:lightning-bolt",
        "unit": "kWh",
        "device_class": "energy",
        "state_class": "measurement"
    },
    "power": {
        "name": "Power",
        "icon": "mdi:flash",
        "unit": "W",
        "device_class": "power",
        "state_class": "measurement"
    },
    "voltage": {
        "name": "Voltage",
        "icon": "mdi:sine-wave",
        "unit": "V",
        "device_class": "voltage",
        "state_class": "measurement"
    },
    "current": {
        "name": "Current",
        "icon": "mdi:current-ac",
        "unit": "A",
        "device_class": "current",
        "state_class": "measurement"
    }
}
