"""Data update coordinator for OneMeter integration."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import OneMeterApiClient
from .const import SENSOR_TO_OBIS_MAP, UPDATE_OFFSET_SECONDS

_LOGGER = logging.getLogger(__name__)


def _validate_api_data(device_data: Any, readings_data: Any) -> None:
    """Validate API data and raise UpdateFailed if invalid.

    Args:
        device_data: Device data from the API
        readings_data: Readings data from the API

    Raises:
        UpdateFailed: If both device_data and readings_data are invalid
    """
    if not device_data and not readings_data:
        raise UpdateFailed("Failed to fetch data from OneMeter API")

    if not device_data:
        _LOGGER.warning("Device data is missing or empty, using only readings data")
    elif not readings_data:
        _LOGGER.warning("Readings data is missing or empty, using only device data")

    # Check for specific data structure integrity
    if device_data and not isinstance(device_data, dict):
        _LOGGER.error("Device data has invalid format: %s", type(device_data))
        raise UpdateFailed("Device data has invalid format")

    if readings_data and not isinstance(readings_data, dict):
        _LOGGER.error("Readings data has invalid format: %s", type(readings_data))
        raise UpdateFailed("Readings data has invalid format")


class OneMeterUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to coordinate updates for OneMeter sensors."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: OneMeterApiClient,
        refresh_interval: int,
        name: str,
        device_id: str,
    ) -> None:
        """Initialize the coordinator with custom update interval."""
        self.client = client
        self.device_id = device_id
        self._refresh_interval_minutes = refresh_interval

        # Calculate the next update time for synchronized updates
        update_interval = self._calculate_update_interval()

        super().__init__(
            hass,
            _LOGGER,
            name=name,
            update_interval=update_interval,
        )

    def _calculate_update_interval(self) -> timedelta:
        """Calculate the time until the next synchronized update."""
        now = dt_util.now()

        # Calculate minutes until the next interval (1, 5, or 15 min)
        minutes_to_sync = self._refresh_interval_minutes - (
            now.minute % self._refresh_interval_minutes
        )

        # If we're already at an exact interval, use the full interval delay
        if minutes_to_sync == self._refresh_interval_minutes:
            minutes_to_sync = 0

        # Calculate seconds until the next interval + offset seconds
        seconds_to_sync = (minutes_to_sync * 60) - now.second + UPDATE_OFFSET_SECONDS

        # If we're too close to the next update time, add a full interval
        if seconds_to_sync < 5:  # If less than 5 seconds away
            seconds_to_sync += self._refresh_interval_minutes * 60

        _LOGGER.debug(
            "Calculated update interval: %s minutes, %s seconds to next sync",
            self._refresh_interval_minutes,
            seconds_to_sync,
        )

        return timedelta(seconds=seconds_to_sync)

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via API and schedule next update at fixed intervals."""
        try:
            # Get device data - essential for most readings
            device_data = await self.client.get_device_data()

            # Simplified validation
            if not device_data or not isinstance(device_data, dict):
                raise UpdateFailed("Invalid or missing device data from OneMeter API")

            # Get detailed readings only if needed and device data is valid
            all_obis_codes = list(set(SENSOR_TO_OBIS_MAP.values()))
            # Consider making this call optional or based on needed sensors
            readings_data = await self.client.get_readings(1, all_obis_codes)

            # Process data if successful
            data: dict[str, Any] = {}

            # Extract all values from device data and readings
            for sensor_key, obis_code in SENSOR_TO_OBIS_MAP.items():
                # Try to get the value from device data first
                value = self.client.extract_device_value(device_data, obis_code)

                # If not found, try to get from readings data
                if value is None and readings_data:
                    value = self.client.extract_reading_value(readings_data, obis_code)

                if value is not None:
                    data[sensor_key] = value

            # Parse and add the separated IR power and baud rate values
            if "uart_params" in data and isinstance(data["uart_params"], str):
                uart_value = data["uart_params"]
                try:
                    # Parse formats like "3/300" or other variants
                    if "/" in uart_value:
                        parts = uart_value.split("/", 1)
                        if len(parts) == 2:
                            ir_power, baud_rate = parts
                            data["ir_power"] = ir_power.strip()
                            # Ensure baud rate is a numeric value
                            data["baud_rate"] = int(baud_rate.strip())
                except (ValueError, TypeError) as err:
                    _LOGGER.debug("Could not parse UART parameters: %s - %s", uart_value, err)
            elif "uart_params" in data and isinstance(data["uart_params"], list):
                # Handle case where uart_params might be a list like [7, 9600]
                try:
                    uart_list = data["uart_params"]
                    if len(uart_list) >= 2:
                        # First element is typically IR power, second is baud rate
                        data["ir_power"] = str(uart_list[0])
                        data["baud_rate"] = int(uart_list[1]) if isinstance(uart_list[1], (int, float, str)) else None
                except (IndexError, ValueError, TypeError) as err:
                    _LOGGER.debug("Could not parse UART parameters list: %s - %s", data["uart_params"], err)

            # Add battery percentage calculated from battery voltage
            try:
                if "battery_voltage" in data and isinstance(
                    data["battery_voltage"], (int, float)
                ):
                    from .helpers import calculate_battery_percentage

                    data["battery_percentage"] = calculate_battery_percentage(
                        data["battery_voltage"]
                    )
            except Exception as err:
                _LOGGER.debug("Error calculating battery percentage: %s", err)

            # Extract monthly usage data if available
            try:
                monthly_data = {
                    "this_month": self.client.get_this_month_usage(device_data),
                    "previous_month": self.client.get_previous_month_usage(device_data),
                }

                # Only add non-None values to the data dictionary
                data.update({k: v for k, v in monthly_data.items() if v is not None})
            except Exception as err:
                _LOGGER.debug("Error extracting monthly usage data: %s", err)

            # Schedule the next update at a precisely timed interval
            next_update = self._calculate_update_interval()
            self.update_interval = next_update

            _LOGGER.debug(
                "Update completed with %d values, next update in %s",
                len(data),
                next_update
            )

            return data

        except Exception as err:
            _LOGGER.error("Error updating OneMeter data: %s", err)
            raise UpdateFailed(f"Error communicating with OneMeter API: {err}") from err
