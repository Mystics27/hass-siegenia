"""Support for Siegenia fans."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.percentage import (
    ordered_list_item_to_percentage,
    percentage_to_ordered_list_item,
)

from .const import AEROPAC_FAN_LEVELS, DOMAIN
from .coordinator import SiegeniaDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# Convert AEROPAC fan levels to ordered list for percentage calculation
ORDERED_FAN_SPEEDS = list(AEROPAC_FAN_LEVELS.keys())[1:]  # Exclude 0 (off)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry, 
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Siegenia fan from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Only add fan entity if we have device info
    if coordinator.data and coordinator.data.get("device_info"):
        async_add_entities([SiegeniaFan(coordinator, entry)])


class SiegeniaFan(CoordinatorEntity, FanEntity):
    """Representation of a Siegenia fan."""

    _attr_has_entity_name = True
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED | 
        FanEntityFeature.TURN_ON | 
        FanEntityFeature.TURN_OFF
    )
    _attr_speed_count = 7  # Level 1-7

    def __init__(
        self, 
        coordinator: SiegeniaDataUpdateCoordinator,
        entry: ConfigEntry
    ) -> None:
        """Initialize the fan."""
        super().__init__(coordinator)
        
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_fan"
        
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
        
        self._attr_name = None  # Use device name

    @property
    def is_on(self) -> bool:
        """Return true if fan is on."""
        if not self.coordinator.data:
            return False
            
        # Check if device is active and fan level > 0
        device_active = self.coordinator.data.get("deviceactive", False)
        fan_level = self.coordinator.data.get("fanlevel", 0)
        
        return device_active and fan_level > 0

    @property
    def percentage(self) -> int:
        """Return the current speed as percentage (mapped from fan levels 1-7)."""
        if not self.coordinator.data:
            return 0
            
        fan_level = self.coordinator.data.get("fanlevel", 0)
        
        if fan_level == 0:
            return 0
        
        # Map fan levels 1-7 to percentage 1-100
        # Level 1 = ~14%, Level 7 = 100%
        return int((fan_level / 7) * 100)

    @property
    def speed_count(self) -> int:
        """Return the number of speeds the fan supports."""
        return 7  # Level 1-7

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the fan."""
        try:
            # If no speed level is selected, use level 4 as default
            if percentage is not None:
                # Convert Percentage to Level 1-7
                fan_level = max(1, min(7, int((percentage / 100) * 7)))
            else:
                fan_level = 4  # Default
                
            _LOGGER.debug("Turning on fan with level %s (from percentage %s)", fan_level, percentage)
            
            # Make sure device is turned on
            await self.coordinator.async_set_device_active(True)
            
            # Set Fan Level
            await self.coordinator.async_set_fan_level(fan_level)
            
        except Exception as err:
            _LOGGER.error("Error turning on fan: %s", err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the fan."""
        try:
            _LOGGER.debug("Turning off fan (setting level to 0)")
            # Turn Device Off = Level 0
            await self.coordinator.async_set_fan_level(0)
            # Turn Device Off
            await self.coordinator.async_set_device_active(False)
        except Exception as err:
            _LOGGER.error("Error turning off fan: %s", err)

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""
        try:
            if percentage == 0:
                await self.async_turn_off()
            else:
                # Convert Percentage to Level 1-7
                fan_level = max(1, min(7, int((percentage / 100) * 7)))
                _LOGGER.debug("Setting fan level %s (from percentage %s)", fan_level, percentage)
                await self.coordinator.async_set_fan_level(fan_level)
        except Exception as err:
            _LOGGER.error("Error setting fan percentage: %s", err)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return {}
            
        attributes = {}
        
        # Add current fan level
        fan_level = self.coordinator.data.get("fanlevel", 0)
        attributes["fan_level"] = fan_level
        attributes["fan_level_name"] = AEROPAC_FAN_LEVELS.get(fan_level, "Unknown")
        
        # Add device active state
        attributes["device_active"] = self.coordinator.data.get("deviceactive", False)
        
        # Add timer information if available
        if "timer" in self.coordinator.data:
            timer_data = self.coordinator.data["timer"]
            if isinstance(timer_data, dict):
                if "remainingtime" in timer_data:
                    remaining = timer_data["remainingtime"]
                    if isinstance(remaining, dict) and "hour" in remaining and "minute" in remaining:
                        attributes["timer_remaining"] = f"{remaining['hour']:02d}:{remaining['minute']:02d}"
                        
                if "enabled" in timer_data:
                    attributes["timer_enabled"] = timer_data["enabled"]
        
        # Add warnings if any
        warnings = self.coordinator.data.get("warnings", [])
        if warnings:
            attributes["warnings"] = warnings
            
        return attributes
