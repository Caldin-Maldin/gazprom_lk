"""Number entity for Gazprom LK."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

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

class GazpromLKNumber(GazpromLKEntity, NumberEntity, RestoreEntity):
    """Representation of a Gazprom LK number input."""
    
    def __init__(self, coordinator: GazpromLKDataUpdateCoordinator) -> None:
        """Initialize number."""
        super().__init__(coordinator)
        self._attr_name = "Показания счетчика"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_indication_input"
        self._attr_icon = "mdi:counter"
        self._attr_native_min_value = 1
        self._attr_native_max_value = 99999
        self._attr_native_step = 1
        self._attr_native_unit_of_measurement = "м³"
        self._attr_mode = "box"
        
        # Инициализируем pending_value в координаторе
        self.coordinator.pending_value = None

    @property
    def native_value(self) -> float | None:
        """Return current value."""
        # Показываем последние переданные показания (из API)
        if not self.coordinator.data:
            return None
        return float(self.coordinator.data.get("ls_value_gas", 0))

    async def async_set_native_value(self, value: float) -> None:
        """Validate and save value to coordinator."""
        # Получаем предыдущие показания
        previous_value = None
        if self.coordinator.data:
            previous_value = float(self.coordinator.data.get("ls_value_gas", 0))
        
        # ПРОВЕРКА 1: Отрицательные значения
        if value < 0:
            error_msg = f"❌ Отрицательные показания недопустимы!\nВведено значение: {value} м³"
            _LOGGER.error(error_msg)
            await self._show_error_notification(error_msg)
            return
        
        # ПРОВЕРКА 2: Нулевые значения
        if value == 0:
            error_msg = f"❌ Нулевые показания недопустимы!\nПоказания должны быть больше 0 м³"
            _LOGGER.error(error_msg)
            await self._show_error_notification(error_msg)
            return
        
        # ПРОВЕРКА 3: Проверка на превышение предыдущих показаний
        if previous_value is not None and value <= previous_value:
            error_msg = (
                f"❌ Ошибка: Новые показания ({value} м³) "
                f"не превышают предыдущие ({previous_value} м³)!\n"
                f"Показания счетчика могут только увеличиваться.\n"
                f"Введите значение больше {previous_value} м³."
            )
            _LOGGER.error(error_msg)
            await self._show_error_notification(error_msg)
            return
        
        # Все проверки пройдены - сохраняем значение
        _LOGGER.info("✅ Сохранено новое значение для отправки: %s м³", value)
        
        # Сохраняем значение в координаторе
        self.coordinator.pending_value = value
        
        # Обновляем состояние
        self.async_write_ha_state()
        
        # Показываем уведомление об успехе
        await self._show_success_notification(value)
    
    async def _show_success_notification(self, value: float) -> None:
        """Show success notification."""
        try:
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "📝 Газпром ЛК",
                    "message": f"✅ Значение {value} м³ сохранено.\nНажмите кнопку 'Передать показания' для отправки.",
                    "notification_id": f"gazprom_value_saved_{self.coordinator.entry.entry_id}",
                },
                blocking=False,
            )
        except Exception as e:
            _LOGGER.debug("Не удалось показать уведомление: %s", e)
    
    async def _show_error_notification(self, message: str) -> None:
        """Show error notification."""
        try:
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "❌ Ошибка ввода показаний",
                    "message": message,
                    "notification_id": f"gazprom_error_{self.coordinator.entry.entry_id}",
                },
                blocking=False,
            )
        except Exception as e:
            _LOGGER.debug("Не удалось показать уведомление об ошибке: %s", e)