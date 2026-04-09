"""Buttons for Gazprom LK."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
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
    """Set up Gazprom LK buttons based on a config entry."""
    coordinator: GazpromLKDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    buttons = [
        GazpromLKButton(coordinator, "update", "Обновить данные", "mdi:refresh"),
        GazpromLKButton(coordinator, "send_indication", "Передать показания", "mdi:send"),
    ]
    
    async_add_entities(buttons)

class GazpromLKButton(GazpromLKEntity, ButtonEntity):
    """Representation of a Gazprom LK button."""
    
    def __init__(
        self,
        coordinator: GazpromLKDataUpdateCoordinator,
        button_type: str,
        name: str,
        icon: str
    ) -> None:
        """Initialize button."""
        super().__init__(coordinator)
        self._button_type = button_type
        self._attr_name = f"{name}"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_button_{button_type}"
        self._attr_icon = icon

    async def async_press(self) -> None:
        """Handle button press."""
        if self._button_type == "update":
            await self.coordinator.async_request_refresh()
            _LOGGER.info("Данные Gazprom LK успешно обновлены")
        elif self._button_type == "send_indication":
            await self._send_indication()

    async def _send_indication(self):
        """Send current indication."""
        device_id = self.coordinator.entry.entry_id
        
        if not self.coordinator.data:
            _LOGGER.error("Нет данных для отправки показаний")
            return
        
        try:
            # Получаем текущие показания
            current_value = float(self.coordinator.data.get("ls_value_gas", 0))
            
            if current_value <= 0:
                _LOGGER.error("Текущие показания некорректны: %s", current_value)
                return
            
            # Отправляем показания
            _LOGGER.info("Отправка показаний: %s м³", current_value)
            result = await self.coordinator.async_send_indication(current_value)
            
            if result.get("success"):
                _LOGGER.info("Показания успешно переданы: %s м³", current_value)
            else:
                _LOGGER.error("Ошибка при передаче показаний: %s", result.get('message'))
                
        except (ValueError, TypeError) as e:
            _LOGGER.error("Некорректное значение показаний: %s", e)