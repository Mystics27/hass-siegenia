"""Support for Siegenia number entities."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import AEROPAC_FAN_LEVELS, DOMAIN
from .coordinator import SiegeniaDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Siegenia number entities from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Only add number entity if we have device info
    if coordinator.data and coordinator.data.get("device_info"):
        async_add_entities([SiegeniaFanLevelNumber(coordinator, entry)])


class SiegeniaFanLevelNumber(CoordinatorEntity, NumberEntity):
    """Representation of Siegenia fan level number entity."""

    _attr_has_entity_name = True
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 0
    _attr_native_max_value = 7
    _attr_native_step = 1
    _attr_icon = "mdi:fan"

    def __init__(
        self,
        coordinator: SiegeniaDataUpdateCoordinator,
        entry: ConfigEntry
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_fan_level"
        
        # Set device info
        device_info = coordinator.data.get("device_info", {})
        device_name = device_info.get("devicename", "Siegenia Device")
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": device_name,
            "manufacturer": "Siegenia",
            "model": device_info.get("type", "Unknown"),
            "sw_version": device_info.get("softwareversion"),
            "hw_version": device_info.get("hardwareversion"),
            "serial_number": device_info.get("serialnr"),
        }
        
        self._attr_name = "fanlevel"
        self._attr_translation_key = "fan_level"

    @property
    def native_value(self) -> int:
        """Return the current fan level."""
        if not self.coordinator.data:
            return 0
        return self.coordinator.data.get("fanlevel", 0)

    async def async_set_native_value(self, value: float) -> None:
        """Set the fan level."""
        try:
            fan_level = int(value)
            _LOGGER.debug("Setting fan level to %s", fan_level)
            
            if fan_level == 0:
                # Turn Device off
                await self.coordinator.async_set_fan_level(0)
                await self.coordinator.async_set_device_active(False)
            else:
                # Turn Device on, then set fan speed level
                await self.coordinator.async_set_device_active(True)
                await self.coordinator.async_set_fan_level(fan_level)
                
        except Exception as err:
            _LOGGER.error("Error setting fan level: %s", err)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return {}
            
        attributes = {}
        fan_level = self.coordinator.data.get("fanlevel", 0)
        
        # Name der aktuellen Stufe
        attributes["level_name"] = AEROPAC_FAN_LEVELS.get(fan_level, "Unknown")
        
        # Gerätestatus
        attributes["device_active"] = self.coordinator.data.get("deviceactive", False)
        
        return attributes
