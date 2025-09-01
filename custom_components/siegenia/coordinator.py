"""Data update coordinator for Siegenia integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_USE_SSL, DOMAIN
from .device import SiegeniaDevice

_LOGGER = logging.getLogger(__name__)


class SiegeniaDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Siegenia device."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        self.entry = entry
        self.device = SiegeniaDevice(
            host=entry.data[CONF_HOST],
            port=entry.data[CONF_PORT],
            username=entry.data[CONF_USERNAME], 
            password=entry.data[CONF_PASSWORD],
            use_ssl=entry.data[CONF_USE_SSL]
        )
        
        # Set up data callback for real-time updates
        self.device.set_data_callback(self._handle_data_update)
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            if not self.device.is_connected:
                await self.device.connect()
                if not await self.device.login():
                    raise UpdateFailed("Failed to login to device")

            # Get current device state and parameters
            device_state = await self.device.get_device_state()
            device_params = await self.device.get_device_params()
            device_info = await self.device.get_device_info()
            
            # Merge all data
            data = {
                **device_state,
                **device_params,
                "device_info": device_info
            }
            
            _LOGGER.debug("Updated data: %s", data)
            return data
            
        except Exception as err:
            _LOGGER.error("Error communicating with device: %s", err)
            raise UpdateFailed(f"Error communicating with device: {err}") from err

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator."""
        if self.device:
            await self.device.disconnect()

    def _handle_data_update(self, data: dict[str, Any]) -> None:
        """Handle real-time data updates from device."""
        _LOGGER.debug("Received real-time update: %s", data)
        if self.data:
            # Update existing data with new values
            self.data.update(data)
            # Trigger update to all listening entities
            self.async_set_updated_data(self.data)

    async def async_set_fan_level(self, level: int) -> None:
        """Set fan level."""
        await self.device.set_fan_level(level)
        # Trigger immediate data refresh
        await self.async_request_refresh()

    async def async_set_device_active(self, active: bool) -> None:
        """Set device active state."""
        await self.device.set_device_active(active)
        # Trigger immediate data refresh  
        await self.async_request_refresh()