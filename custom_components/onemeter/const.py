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

# OBIS Codes
OBIS_ENERGY_PLUS = "1_8_0"      # Positive active energy (consumption) total
OBIS_ENERGY_MINUS = "2_8_0"     # Negative active energy (production) total
OBIS_ENERGY_R1 = "5_8_0"        # Reactive energy R1 component 
OBIS_ENERGY_R4 = "8_8_0"        # Reactive energy R4 component
OBIS_ENERGY_ABS = "15_8_0"      # Absolute active energy
OBIS_POWER = "16_7_0"           # Instantaneous active power
OBIS_BATTERY_VOLTAGE = "S_1_1_2" # Device battery status
OBIS_METER_SERIAL = "C_1_0"      # Meter serial number
OBIS_UART_PARAMS = "S_1_1_8"     # Meter communication parameters
OBIS_METER_ERROR = "F_F_0"       # Meter error status
OBIS_PHYSICAL_ADDRESS = "0_0_0"  # Device address
OBIS_SUCCESSFUL_READINGS = "S_1_1_6" # Successful readouts since restart
OBIS_FAILED_READINGS_1 = "S_1_1_7"  # Failed readout attempts on 1st/2nd message
OBIS_FAILED_READINGS_2 = "S_1_1_19" # Failed readouts since restart
OBIS_TARIFF = "0_2_2"           # Active tariff

# Additional OBIS codes from documentation
OBIS_ENERGY_PLUS_T1 = "1_8_1"   # Positive active energy in tariff I
OBIS_ENERGY_PLUS_T2 = "1_8_2"   # Positive active energy in tariff II
OBIS_ENERGY_PLUS_T3 = "1_8_3"   # Positive active energy in tariff III
OBIS_ENERGY_PLUS_T4 = "1_8_4"   # Positive active energy in tariff IV

OBIS_ENERGY_MINUS_T1 = "2_8_1"  # Negative active energy in tariff I
OBIS_ENERGY_MINUS_T2 = "2_8_2"  # Negative active energy in tariff II
OBIS_ENERGY_MINUS_T3 = "2_8_3"  # Negative active energy in tariff III
OBIS_ENERGY_MINUS_T4 = "2_8_4"  # Negative active energy in tariff IV

OBIS_TIME = "0_9_1"             # Time
OBIS_DATE = "0_9_2"             # Date
OBIS_ENERGY_R1_T1 = "5_8_1"     # Reactive energy in 1st quadrant in tariff I
OBIS_ENERGY_R1_T2 = "5_8_2"     # Reactive energy in 1st quadrant in tariff II
OBIS_ENERGY_R1_T3 = "5_8_3"     # Reactive energy in 1st quadrant in tariff III
OBIS_ENERGY_R1_T4 = "5_8_4"     # Reactive energy in 1st quadrant in tariff IV

OBIS_ENERGY_R4_T1 = "8_8_1"     # Reactive energy in 4th quadrant in tariff I
OBIS_ENERGY_R4_T2 = "8_8_2"     # Reactive energy in 4th quadrant in tariff II
OBIS_ENERGY_R4_T3 = "8_8_3"     # Reactive energy in 4th quadrant in tariff III
OBIS_ENERGY_R4_T4 = "8_8_4"     # Reactive energy in 4th quadrant in tariff IV

OBIS_ACTIVE_DEMAND = "1_4_0"    # Positive active demand in current demand period
OBIS_ACTIVE_MAX_DEMAND = "1_2_1" # Positive active cumulative maximum demand
OBIS_OPTICAL_PORT_SERIAL = "C_90_1" # Optical port serial number
OBIS_TEMPERATURE = "S_1_1_9"    # Temperature
OBIS_READOUT_TIMESTAMP = "S_1_1_4" # Readout timestamp (real)
OBIS_READOUT_TIMESTAMP_CORRECTED = "S_1_1_10" # Readout timestamp (corrected)
OBIS_ENERGY_CONSUMPTION_BLINK = "S_1_1_12" # Energy consumption (based on blink measurements)
OBIS_DEVICE_STATUS = "S_1_1_16" # Status of OneMeter Device

# API Configuration
API_BASE_URL = "https://cloud.onemeter.com/api/"
API_TIMEOUT = 30

# Icons
ICON_ENERGY = "mdi:lightning-bolt"
ICON_VOLTAGE = "mdi:flash"
ICON_BATTERY = "mdi:battery"
ICON_TIMESTAMP = "mdi:clock"
ICON_MONTH = "mdi:calendar-month"
ICON_TEMPERATURE = "mdi:thermometer"
ICON_DEMAND = "mdi:gauge"
ICON_COUNTER = "mdi:counter"
ICON_ERROR = "mdi:alert-circle"
ICON_INFO = "mdi:information"
ICON_SERIAL = "mdi:barcode"

# Entity category
DIAGNOSTIC_ENTITIES = ["voltage", "battery_level", "last_update", "meter_serial", "optical_port_serial", 
                      "uart_params", "meter_error", "physical_address", "successful_readings", 
                      "failed_readings_1", "failed_readings_2", "temperature", "device_status",
                      "readout_timestamp", "readout_timestamp_corrected"]

# API Response keys
RESP_DEVICES = "devices"
RESP_LAST_READING = "lastReading"
RESP_OBIS = "OBIS"
RESP_USAGE = "usage"
RESP_THIS_MONTH = "thisMonth"
RESP_PREV_MONTH = "previousMonth"
