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
    ATTR_COUNTER_LAST_VALUE, 
    ATTR_LAST_VALUE_DATE,  
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
        GazpromLKNumericSensor(coordinator, "counter_last_value", "Предыдущие показания", "mdi:counter", "м³", 1),  
        # Текстовые сенсоры - используем отдельный класс
        GazpromLKTextSensor(coordinator, "counter_name", "Название счетчика", "mdi:identifier"),
        GazpromLKTextSensor(coordinator, "last_indication_previous_date", "Дата предыдущей передачи", "mdi:calendar-clock"),
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
            elif self._sensor_type == "counter_last_value":
                return float(data.get("ls_last_value_gas", 0)) 
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
        elif self._sensor_type == "counter_last_value":
            attrs[ATTR_LAST_VALUE_DATE] = data.get("ls_last_value_date", "") 
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
        
        # Для дат используем device_class TIMESTAMP
        if sensor_type in ["last_indication_date", "last_indication_previous_date"]:
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
                # Дата последней передачи
                date_str = data.get("ls_value_date", "")
                return self._parse_date(date_str)
            
            elif self._sensor_type == "last_indication_previous_date":
                # Дата предыдущей передачи
                date_str = data.get("ls_last_value_date", "")
                return self._parse_date(date_str)
            
        except (ValueError, TypeError, AttributeError) as e:
            _LOGGER.error("Ошибка в сенсоре %s: %s", self._sensor_type, e)
            return None
        
        return None
    
 

    def _parse_date(self, date_str: str) -> datetime | str | None:
        """Parse date string to datetime object."""
        if not date_str or not date_str.strip():
            return None
        
        try:
            # Формат из API: "2026-04-11T00:00:00"
            if 'T' in date_str:
                # Убираем время, оставляем только дату
                date_part = date_str.split('T')[0]
                date_obj = datetime.strptime(date_part, "%Y-%m-%d")
                # Делаем дату timezone-aware (локальное время)
                if date_obj.tzinfo is None:
                    date_obj = date_obj.astimezone()
                _LOGGER.debug("Распаршена дата '%s' -> %s", date_str, date_obj)
                return date_obj
            
            # Другие форматы на всякий случай
            formats = [
                "%d.%m.%Y %H:%M:%S",  # 11.04.2026 14:30:00
                "%Y-%m-%d %H:%M:%S",  # 2026-04-11 14:30:00
                "%d.%m.%Y",           # 11.04.2026
                "%Y-%m-%d",           # 2026-04-11
            ]
            
            for fmt in formats:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    if date_obj.tzinfo is None:
                        date_obj = date_obj.astimezone()
                    _LOGGER.debug("Распаршена дата '%s' в формате '%s': %s", date_str, fmt, date_obj)
                    return date_obj
                except ValueError:
                    continue
            
            # Если ничего не подошло, возвращаем строку
            _LOGGER.warning("Не удалось распарсить дату: %s", date_str)
            return date_str
            
        except (ValueError, TypeError) as e:
            _LOGGER.warning("Ошибка парсинга даты '%s': %s", date_str, e)
            return date_str if date_str else None



    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        if not self.coordinator.data:
            return {}
            
        data = self.coordinator.data
        
        attrs = {
            ATTR_LSID: data.get("lsid", ""),
            "counter_id": data.get("counterid", ""),
        }
        
        if self._sensor_type == "counter_name":
            # Информация о счетчике
            attrs.update({
                "last_value": data.get("ls_value_gas", 0),
                "last_value_date": data.get("ls_value_date", ""),
                "previous_value": data.get("ls_last_value_gas", 0),
                "previous_value_date": data.get("ls_last_value_date", ""),
                "rate": data.get("ls_rate_gas", 0),
            })
            
        elif self._sensor_type == "last_indication_date":
            # Информация о последней передаче
            attrs.update({
                "last_value": data.get("ls_value_gas", 0),
                "previous_value": data.get("ls_last_value_gas", 0),
                "counter_name": data.get("ls_counter", ""),
                "rate": data.get("ls_rate_gas", 0),
                "raw_date_string": data.get("ls_value_date", ""),
            })
            
        elif self._sensor_type == "last_indication_previous_date":
            # Информация о предыдущей передаче
            attrs.update({
                "previous_value": data.get("ls_last_value_gas", 0),
                "current_value": data.get("ls_value_gas", 0),
                "counter_name": data.get("ls_counter", ""),
                "rate": data.get("ls_rate_gas", 0),
                "raw_date_string": data.get("ls_last_value_date", ""),
            })
        
        return attrs
