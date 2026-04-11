"""Sensors for Gazprom LK."""
from __future__ import annotations

import logging
from typing import Any
from datetime import datetime

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import EntityCategory

from .const import (
    DOMAIN,
    ATTR_BALANCE_ALL,
    ATTR_BALANCE_GAS,
    ATTR_COUNTER_NAME,
    ATTR_COUNTER_VALUE,
    ATTR_COUNTER_RATE,
    ATTR_VALUE_DATE,
    ATTR_LSID,
    ATTR_COUNTERID,
    ATTR_COUNTER_FULL_NAME,
    ATTR_LAST_INDICATION_DATE
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
        GazpromLKNumericSensor(coordinator, "balance_all", "Общая задолженность", "mdi:currency-rub", "RUB", 2),
        GazpromLKNumericSensor(coordinator, "balance_gas", "Задолженность за газ", "mdi:currency-rub", "RUB", 2),
        GazpromLKNumericSensor(coordinator, "counter_value", "Показания счетчика", "mdi:counter", "m³", 1),
        GazpromLKNumericSensor(coordinator, "counter_rate", "Расход газа", "mdi:gas-burner", "m³", 1),
        
        # Текстовые сенсоры - используем отдельный класс
        GazpromLKTextSensor(coordinator, "counter_name", "Название счетчика", "mdi:identifier"),
        GazpromLKTextSensor(coordinator, "last_indication_date", "Дата последней передачи", "mdi:calendar-clock"),
    ]
    
    async_add_entities(sensors)

class GazpromLKNumericSensor(GazpromLKEntity, SensorEntity):
    """Representation of a numeric Gazprom LK sensor."""
    
    def __init__(
        self,
        coordinator: GazpromLKDataUpdateCoordinator,
        sensor_type: str,
        name: str,
        icon: str,
        unit: str,
        precision: int = 1
    ) -> None:
        """Initialize numeric sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_name = f"{name}"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{sensor_type}"
        self._attr_icon = icon
        self._attr_native_unit_of_measurement = unit
        self._attr_suggested_display_precision = precision
        
        if unit == "RUB":
            self._attr_device_class = SensorDeviceClass.MONETARY

    @property
    def native_value(self) -> float | None:
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

class GazpromLKTextSensor(GazpromLKEntity, SensorEntity):
    """Representation of a text Gazprom LK sensor."""
    
    def __init__(
        self,
        coordinator: GazpromLKDataUpdateCoordinator,
        sensor_type: str,
        name: str,
        icon: str,
    ) -> None:
        """Initialize text sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_name = f"{name}"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{sensor_type}"
        self._attr_icon = icon
        # Для даты используем device_class TIMESTAMP
        if sensor_type == "last_indication_date":
            self._attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self) -> str | datetime | None:
        """Return state of sensor."""
        if not self.coordinator.data:
            return None
            
        data = self.coordinator.data
        
        try:
            if self._sensor_type == "counter_name":
                # Возвращаем название счетчика как строку
                return data.get("ls_counter", "Неизвестно")
            elif self._sensor_type == "last_indication_date":
                # Преобразуем дату в datetime объект
                date_str = data.get("ls_value_date", "")
                if date_str and date_str.strip():
                    try:
                        # Пробуем разные форматы даты
                        for fmt in ["%d.%m.%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d.%m.%Y", "%Y-%m-%d"]:
                            try:
                                date_obj = datetime.strptime(date_str, fmt)
                                # Возвращаем datetime объект, а не строку!
                                return date_obj
                            except ValueError:
                                continue
                        
                        # Пробуем парсить ISO формат с Z (UTC)
                        if date_str.endswith('Z'):
                            date_str = date_str.replace('Z', '+00:00')
                            date_obj = datetime.fromisoformat(date_str)
                            return date_obj
                        
                        # Если ничего не подошло, логируем и возвращаем None
                        _LOGGER.warning("Не удалось распарсить дату: %s", date_str)
                        return None
                    except (ValueError, TypeError) as e:
                        _LOGGER.warning("Ошибка парсинга даты %s: %s", date_str, e)
                        return None
                return None
        except (ValueError, TypeError, AttributeError) as e:
            _LOGGER.error("Ошибка в сенсоре %s: %s", self._sensor_type, e)
            return None
        
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        if not self.coordinator.data:
            return {}
            
        data = self.coordinator.data
        
        attrs = {}
        if self._sensor_type == "counter_name":
            # Добавляем дополнительную информацию о счетчике
            attrs["counter_id"] = data.get("counterid", "")
            attrs["last_value"] = data.get("ls_value_gas", 0)
            attrs["last_value_date"] = data.get("ls_value_date", "")
            attrs["rate"] = data.get("ls_rate_gas", 0)
        elif self._sensor_type == "last_indication_date":
            # Добавляем информацию о последних показаниях
            attrs["last_value"] = data.get("ls_value_gas", 0)
            attrs["counter_name"] = data.get("ls_counter", "")
            attrs["counter_id"] = data.get("counterid", "")
            attrs["rate"] = data.get("ls_rate_gas", 0)
            # Добавляем сырую строку даты для отладки
            attrs["raw_date_string"] = data.get("ls_value_date", "")
            
        attrs[ATTR_LSID] = data.get("lsid", "")
        
        return attrs