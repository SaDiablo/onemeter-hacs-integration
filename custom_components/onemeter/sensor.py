"""Support for OneMeter sensors."""
import logging
from datetime import timedelta
import async_timeout

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import OneMeterApiClient
from .const import DOMAIN, SENSOR_TYPES, SCAN_INTERVAL, CONF_API_KEY

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the OneMeter sensors."""
    username = config_entry.data[CONF_USERNAME]
    password = config_entry.data[CONF_PASSWORD]
    api_key = config_entry.data.get(CONF_API_KEY)
    
    # Create API client
    client = OneMeterApiClient(username, password, api_key)
    
    async def fetch_data():
        """Fetch data from the OneMeter API."""
        try:
            async with async_timeout.timeout(30):
                data = await client.get_meter_data()
                if data is None:
                    raise UpdateFailed("Failed to fetch data from OneMeter API")
                
                # Transform API response to match sensor types
                transformed_data = {}
                if "energy" in data:
                    transformed_data["energy"] = float(data["energy"])
                if "power" in data:
                    transformed_data["power"] = float(data["power"])
                if "voltage" in data:
                    transformed_data["voltage"] = float(data["voltage"])
                if "current" in data:
                    transformed_data["current"] = float(data["current"])
                    
                return transformed_data
        except Exception as err:
            raise UpdateFailed(f"Error communicating with OneMeter API: {err}")
    
    # Create update coordinator
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="onemeter",
        update_method=fetch_data,
        update_interval=SCAN_INTERVAL,
    )
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    # Create entities
    entities = []
    for sensor_type, sensor_info in SENSOR_TYPES.items():
        if sensor_type in coordinator.data:
            description = SensorEntityDescription(
                key=sensor_type,
                name=sensor_info["name"],
                native_unit_of_measurement=sensor_info["unit"],
                icon=sensor_info["icon"],
                device_class=sensor_info["device_class"],
                state_class=sensor_info["state_class"],
            )
            entities.append(OneMeterSensor(coordinator, description, config_entry.entry_id))
    
    async_add_entities(entities)


class OneMeterSensor(SensorEntity):
    """Representation of a OneMeter sensor."""

    def __init__(self, coordinator, description, entry_id):
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": "OneMeter Energy Monitor",
            "manufacturer": "OneMeter",
            "model": "Cloud Energy Monitor",
            "sw_version": "1.0",
        }
    
    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get(self.entity_description.key)
    
    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
        
    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self._handle_coordinator_update)
        )