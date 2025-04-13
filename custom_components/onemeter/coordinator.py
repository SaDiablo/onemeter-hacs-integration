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
    """Validate API data and raise UpdateFailed if invalid."""
    if not (device_data or readings_data):
        raise UpdateFailed("Failed to fetch data from OneMeter API")


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
            # Get device data for all readings
            device_data = await self.client.get_device_data()

            # Get detailed readings with all OBIS codes
            all_obis_codes = list(set(SENSOR_TO_OBIS_MAP.values()))
            readings_data = await self.client.get_readings(1, all_obis_codes)

            # Validate the data
            _validate_api_data(device_data, readings_data)
        except Exception as err:
            _LOGGER.error("Error updating OneMeter data: %s", err)
            raise UpdateFailed(f"Error communicating with OneMeter API: {err}") from err
        else:
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

            # Add battery percentage calculated from battery voltage
            if "battery_voltage" in data and isinstance(
                data["battery_voltage"], (int, float)
            ):
                from .helpers import calculate_battery_percentage

                data["battery_percentage"] = calculate_battery_percentage(
                    data["battery_voltage"]
                )

            # Also extract monthly usage data if available
            data["this_month"] = self.client.get_this_month_usage(device_data)
            data["previous_month"] = self.client.get_previous_month_usage(device_data)

            # Schedule the next update at a precisely timed interval
            next_update = self._calculate_update_interval()
            self.update_interval = next_update

            _LOGGER.debug("Next update scheduled in %s", next_update)

            return data
