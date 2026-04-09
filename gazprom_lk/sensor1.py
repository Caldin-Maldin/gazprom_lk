"""Sensors for Gazprom LK."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    ATTR_BALANCE_ALL,
    ATTR_BALANCE_GAS,
    ATTR_COUNTER_NAME,
    ATTR_COUNTER_VALUE,
    ATTR_COUNTER_RATE,
    ATTR_VALUE_DATE,
    ATTR_LSID,
    ATTR_COUNTERID
)
from .coordinator import GazpromLKDataUpdateCoordinator
from .entity import GazpromLKEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Gazprom LK sensors based on a config entry."""
    coordinator: GazpromLKDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    sensors = [
        GazpromLKSensor(coordinator, "balance_all", "Общая задолженность", "mdi:mdi:currency-rub", "RUB"),
        GazpromLKSensor(coordinator, "balance_gas", "Задолженность за газ", "mdi:gas-cylinder", "RUB"),
        GazpromLKSensor(coordinator, "counter_value", "Показания счетчика", "mdi:counter", "m³"),
        GazpromLKSensor(coordinator, "counter_rate", "Расход газа", "mdi:counter", "m³"),
    ]
    
    async_add_entities(sensors)

class GazpromLKSensor(GazpromLKEntity, SensorEntity):
    """Representation of a Gazprom LK sensor."""
    
    def __init__(
        self,
        coordinator: GazpromLKDataUpdateCoordinator,
        sensor_type: str,
        name: str,
        icon: str,
        unit: str
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_name = f"{name}"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{sensor_type}"
        self._attr_icon = icon
        self._attr_native_unit_of_measurement = unit
        
        if unit == "RUB":
            self._attr_device_class = SensorDeviceClass.MONETARY
            self._attr_suggested_display_precision = 2
        elif unit == "m³":
            self._attr_suggested_display_precision = 3
        elif "RUB/m³" in unit:
            self._attr_suggested_display_precision = 5

    @property
    def native_value(self) -> float | str | None:
        """Return state of sensor."""
        if not self.coordinator.data:
            return None
            
        data = self.coordinator.data
        
        try:
            if self._sensor_type == "balance_all":
                return float(data.get("ls_balance_all", 0))
            elif self._sensor_type == "balance_gas":
                return float(data.get("ls_balance_gas", 0))
            elif self._sensor_type == "counter_value":
                return float(data.get("ls_value_gas", 0))
            elif self._sensor_type == "counter_rate":
                return float(data.get("ls_rate_gas", 0))
        except (ValueError, TypeError):
            return None
        
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        if not self.coordinator.data:
            return {}
            
        data = self.coordinator.data
        
        attrs = {}
        if self._sensor_type == "counter_value":
            attrs[ATTR_VALUE_DATE] = data.get("ls_value_date", "")
            attrs[ATTR_COUNTER_NAME] = data.get("ls_counter", "")
        elif self._sensor_type == "counter_rate":
            attrs[ATTR_VALUE_DATE] = data.get("ls_value_date", "")
            
        attrs[ATTR_LSID] = data.get("lsid", "")
        attrs[ATTR_COUNTERID] = data.get("counterid", "")
        
        return attrs