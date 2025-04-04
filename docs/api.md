# API Documentation

This document provides information about the OneMeter Cloud API that powers this integration and how you can interact with it programmatically.

## OneMeter Cloud API

The OneMeter Cloud Integration uses the official OneMeter Cloud API to retrieve data from your smart meter. Understanding this API can help you diagnose issues or develop custom integrations.

### API Endpoints

The integration uses the following main endpoints:

```
https://cloud.onemeter.com/api/devices/             # List all devices
https://cloud.onemeter.com/api/devices/<DEVICE_ID>  # Get device details
```

These endpoints return comprehensive information about your devices, including:
- Current readings from the meter
- Historical usage data
- Device configuration
- Battery status

### Authentication

All API requests require authentication using an API key. The key is passed in the HTTP request header:

```
Authorization: <API_KEY>
```

The integration securely stores your API key in Home Assistant's encrypted storage.

### Data Format

The API returns data in JSON format. Here's a simplified example of the response structure:

```json
{
  "lastReading": {
    "OBIS": {
      "1_8_0": 12345.67,     // Energy A+ (total)
      "2_8_0": 0,            // Energy A- (total) 
      "5_8_0": 2305.99,      // Energy R1 (total)
      "8_8_0": 3061.36,      // Energy R4 (total)
      "15_8_0": 12345.67,    // Energy |A| (total)
      "16_7_0": 0.41,        // Instantaneous Power
      "S_1_1_2": 3.09,       // Battery Voltage
      "C_1_0": "11722779",   // Meter Serial Number
      "0_2_2": "G11"         // Tariff
    }
  },
  "usage": {
    "thisMonth": 123.45,
    "previousMonth": 456.78
  }
}
```

## Integration API Implementation

The integration handles the API communication automatically:

1. During setup, it uses your API key to call the `/devices/` endpoint to retrieve a list of all your devices
2. It presents these devices in the UI for you to select which one(s) to add
3. After setup, it periodically queries the `/devices/<DEVICE_ID>` endpoint based on your configured update interval
4. It extracts the relevant sensor values from the API response and makes them available in Home Assistant

## Using the API in Custom Scripts

If you want to create custom scripts to interact with the OneMeter API, here's a Python example:

```python
import requests
import json

API_KEY = "your_api_key_here"
DEVICE_ID = "your_device_id_here"
API_URL = f"https://cloud.onemeter.com/api/devices/{DEVICE_ID}"

headers = {
    "Authorization": API_KEY
}

response = requests.get(API_URL, headers=headers)

if response.status_code == 200:
    data = response.json()
    
    # Get current power usage
    power = data["lastReading"]["OBIS"].get("16_7_0", 0)
    print(f"Current power usage: {power} kW")
    
    # Get total energy consumption
    energy = data["lastReading"]["OBIS"].get("1_8_0", 0)
    print(f"Total energy consumption: {energy} kWh")
    
    # Get this month's usage
    this_month = data["usage"].get("thisMonth", 0)
    print(f"This month's usage: {this_month} kWh")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

## API Rate Limits

The OneMeter Cloud API has rate limits to prevent excessive requests. While the exact limits are not publicly documented, it's recommended to:

- Keep requests to a minimum (no more than 1 request per minute)
- Use caching where possible
- Handle rate limiting errors gracefully

If you encounter HTTP 429 responses, your application is being rate-limited and should reduce the request frequency.

## Integration API Reference

The OneMeter integration's API client is located in `custom_components/onemeter/api.py`. This module provides the following key functions:

### OneMeterApiClient

The main client class that handles communication with the OneMeter Cloud API:

```python
class OneMeterApiClient:
    """API client for OneMeter Cloud."""
    
    def __init__(self, device_id, api_key):
        """Initialize the API client."""
        
    async def get_all_devices(self):
        """Fetch list of devices from OneMeter API."""
        
    async def get_device_data(self):
        """Fetch current device data."""
        
    async def get_readings(self, hours, obis_codes):
        """Fetch historical readings."""
        
    def extract_device_value(self, device_data, obis_code):
        """Extract a specific value from device data."""
```

### OBIS Constants

The integration defines constants for commonly used OBIS codes:

```python
OBIS_ENERGY_PLUS = "1_8_0"      # Positive active energy (consumption)
OBIS_ENERGY_MINUS = "2_8_0"     # Negative active energy (production)
OBIS_ENERGY_R1 = "5_8_0"        # Reactive energy R1 component
OBIS_ENERGY_R4 = "8_8_0"        # Reactive energy R4 component
OBIS_ENERGY_ABS = "15_8_0"      # Absolute active energy
OBIS_POWER = "16_7_0"           # Instantaneous active power
OBIS_BATTERY_VOLTAGE = "S_1_1_2" # Battery voltage
OBIS_METER_SERIAL = "C_1_0"     # Meter serial number
OBIS_TARIFF = "0_2_2"           # Active tariff
```

## Further Resources

- [OneMeter Cloud Website](https://cloud.onemeter.com/)
- [Home Assistant REST Sensor Documentation](https://www.home-assistant.io/integrations/rest/)