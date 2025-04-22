"""Base entity for OneMeter integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
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
        self._device_id = device_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        data = self.coordinator.data if self.coordinator.data else {}

        # Extract device information from coordinator data
        firmware_version = data.get("firmware_version") or "Unknown"
        hardware_version = data.get("hardware_version") or "Unknown"
        serial_number = data.get("meter_serial") or self._device_id
        mac_address = data.get("mac_address") or data.get("physical_address")

        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name="OneMeter Energy Monitor",
            manufacturer="OneMeter",
            model=f"Cloud Energy Monitor {hardware_version}",
            sw_version=firmware_version,
            hw_version=hardware_version,
            serial_number=serial_number,
            connections={("mac", mac_address)} if mac_address else None,
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.data is not None
