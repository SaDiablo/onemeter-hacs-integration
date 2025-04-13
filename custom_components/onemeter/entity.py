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
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name="OneMeter Energy Monitor",
            manufacturer="OneMeter",
            model="Cloud Energy Monitor",
            sw_version="1.0",
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.data is not None
