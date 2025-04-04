"""Constants for the OneMeter Cloud integration."""
from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "onemeter"

# Configuration
CONF_DEVICE_ID = "device_id"
CONF_API_KEY = "api_key"

# Platforms
PLATFORMS = [Platform.SENSOR]

# Update interval (15 minutes as recommended in API docs)
SCAN_INTERVAL = timedelta(minutes=15)

# Default name
DEFAULT_NAME = "OneMeter"

# OBIS Code groups
OBIS_GROUP_ENERGY = [
    "15_8_0",  # Energy A+ (total)
    "15_8_1",  # Energy A+ (phase 1) 
    "F_8_0",   # Total energy (alternate code)
]

OBIS_GROUP_VOLTAGE = [
    "S_1_1_2",  # Battery voltage
]

OBIS_GROUP_BATTERY = [
    "S_1_1_6",  # Battery level
]

OBIS_GROUP_TIMESTAMP = [
    "S_1_1_4",  # Last reading timestamp
]

# Icons
ICON_ENERGY = "mdi:lightning-bolt"
ICON_VOLTAGE = "mdi:flash"
ICON_BATTERY = "mdi:battery"
ICON_TIMESTAMP = "mdi:clock"
ICON_MONTH = "mdi:calendar-month"

# Entity category
DIAGNOSTIC_ENTITIES = ["voltage", "battery_level", "last_update"]

# API Response keys
RESP_DEVICES = "devices"
RESP_LAST_READING = "lastReading"
RESP_OBIS = "OBIS"
RESP_USAGE = "usage"
RESP_THIS_MONTH = "thisMonth"
RESP_PREV_MONTH = "previousMonth"
