"""Number entity for Gazprom LK."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import GazpromLKDataUpdateCoordinator
from .entity import GazpromLKEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Gazprom LK number based on a config entry."""
    coordinator: GazpromLKDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    numbers = [
        GazpromLKNumber(coordinator),
    ]
    
    async_add_entities(numbers)

class GazpromLKNumber(GazpromLKEntity, NumberEntity):
    """Representation of a Gazprom LK number input."""
    
    def __init__(self, coordinator: GazpromLKDataUpdateCoordinator) -> None:
        """Initialize number."""
        super().__init__(coordinator)
        self._attr_name = "Показания счетчика"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_indication_input"
        self._attr_icon = "mdi:counter"
        self._attr_native_min_value = 0
        self._attr_native_max_value = 99999
        self._attr_native_step = 0.001
        self._attr_native_unit_of_measurement = "m³"
        self._attr_mode = "box"

    @property
    def native_value(self) -> float | None:
        """Return current value."""
        if not self.coordinator.data:
            return None
        return float(self.coordinator.data.get("ls_value_gas", 0))

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        result = await self.coordinator.async_send_indication(value)
        
        if not result.get("success"):
            _LOGGER.error("Failed to send indication: %s", result.get("message"))