"""Base entity for OneMeter integration."""

from __future__ import annotations

import logging
from typing import Any, Final

from homeassistant.helpers.device_registry import DeviceInfo, format_mac
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import OneMeterUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class OneMeterEntity(CoordinatorEntity[dict[str, Any]]):
    """Base entity for OneMeter integration."""

    def __init__(
        self,
        coordinator: OneMeterUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._device_id: Final = device_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        data = self.coordinator.data if self.coordinator.data else {}

        # Extract device information from coordinator data
        firmware_version = data.get("firmware_version") or "Unknown"
        hardware_version = data.get("hardware_version") or "Unknown"
        serial_number = data.get("meter_serial") or self._device_id

        # Format MAC address if available
        mac_address = None
        if raw_mac := (data.get("mac_address") or data.get("physical_address")):
            try:
                mac_address = format_mac(raw_mac)
            except ValueError:
                # If we can't format it, use it as-is
                mac_address = raw_mac

        # Build device info dictionary
        device_info_dict = DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name="OneMeter Energy Monitor",
            manufacturer="OneMeter",
        )

        # Only include model with hardware version if it's not "Unknown"
        if hardware_version != "Unknown":
            device_info_dict["model"] = f"Cloud Energy Monitor {hardware_version}"
        else:
            device_info_dict["model"] = "Cloud Energy Monitor"

        # Add firmware version only if not "Unknown"
        if firmware_version != "Unknown":
            device_info_dict["sw_version"] = firmware_version

        # Add hardware version only if not "Unknown"
        if hardware_version != "Unknown":
            device_info_dict["hw_version"] = hardware_version

        # Add serial number if available
        if serial_number:
            device_info_dict["serial_number"] = serial_number

        # Add MAC address connection if available
        if mac_address:
            device_info_dict["connections"] = {("mac", mac_address)}

        return device_info_dict

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.data is not None
