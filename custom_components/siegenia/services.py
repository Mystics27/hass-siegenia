"""Services for Siegenia integration."""
from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.service import async_extract_entity_ids

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SERVICE_SET_FAN_LEVEL = "set_fan_level"

SET_FAN_LEVEL_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_ids,
        vol.Required("level"): vol.All(vol.Coerce(int), vol.Range(min=0, max=7)),
    }
)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for Siegenia integration."""

    async def async_set_fan_level(call: ServiceCall) -> None:
        """Service to set exact fan level."""
        entity_ids = call.data["entity_id"]
        level = call.data["level"]
        
        for entity_id in entity_ids:
            # Get the coordinator from the entity
            entity = hass.data["entity_registry"].async_get(entity_id)
            if not entity or entity.platform != DOMAIN:
                continue
                
            # Find coordinator for this entity
            for entry_id, coordinator in hass.data[DOMAIN].items():
                if hasattr(coordinator, "async_set_fan_level"):
                    await coordinator.async_set_fan_level(level)
                    break

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_FAN_LEVEL,
        async_set_fan_level,
        schema=SET_FAN_LEVEL_SCHEMA,
    )