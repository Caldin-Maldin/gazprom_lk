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
            await self._handle_update()
        elif self._button_type == "send_indication":
            await self._handle_send()

    async def _handle_update(self):
        """Handle update button press."""
        await self.coordinator.async_request_refresh()
        _LOGGER.info("Данные Gazprom LK успешно обновлены")
        await self._show_notification("✅ Данные успешно обновлены")

    async def _handle_send(self):
        """Handle send indication button press with validation."""
        # Получаем значение из координатора (которое установил number)
        value_to_send = getattr(self.coordinator, 'pending_value', None)
        
        _LOGGER.info("📤 Получено значение из pending_value: %s", value_to_send)
        
        # Если в pending_value нет значения, пробуем получить из number entity
        if value_to_send is None:
            _LOGGER.warning("pending_value пуст, ищем number entity...")
            for entity_id in self.hass.states.async_entity_ids("number"):
                if self.coordinator.entry.entry_id in entity_id:
                    number_state = self.hass.states.get(entity_id)
                    if number_state is not None:
                        try:
                            value_to_send = float(number_state.state)
                            _LOGGER.info("Найдено значение в number entity %s: %s", entity_id, value_to_send)
                            break
                        except (ValueError, TypeError):
                            pass
        
        # Проверка на наличие значения
        if value_to_send is None:
            error_msg = "❌ Нет показаний для отправки!\nВведите показания в поле ввода."
            _LOGGER.error(error_msg)
            await self._show_notification(error_msg, is_error=True)
            return
        
        # Получаем предыдущие показания
        previous_value = None
        if self.coordinator.data:
            previous_value = float(self.coordinator.data.get("ls_value_gas", 0))
        
        # ПРОВЕРКА 1: Отрицательные значения
        if value_to_send < 0:
            error_msg = f"❌ Невозможно передать отрицательные показания: {value_to_send} м³"
            _LOGGER.error(error_msg)
            await self._show_notification(error_msg, is_error=True)
            return
        
        # ПРОВЕРКА 2: Нулевые значения
        if value_to_send == 0:
            error_msg = "❌ Невозможно передать нулевые показания!\nПоказания должны быть больше 0 м³."
            _LOGGER.error(error_msg)
            await self._show_notification(error_msg, is_error=True)
            return
        
        # ПРОВЕРКА 3: Показания должны быть больше предыдущих
        if previous_value is not None and value_to_send <= previous_value:
            error_msg = (
                f"❌ Ошибка: Новые показания ({value_to_send} м³) "
                f"не превышают предыдущие ({previous_value} м³)!\n"
                f"Показания счетчика могут только увеличиваться.\n"
                f"Введите значение больше {previous_value} м³."
            )
            _LOGGER.error(error_msg)
            await self._show_notification(error_msg, is_error=True)
            return
        
        # ПРОВЕРКА 4: Слишком большой скачок (более 1000 м³) - только предупреждение
        if previous_value is not None and (value_to_send - previous_value) > 1000:
            warning_msg = (
                f"⚠️ Внимание: Расход газа составил {value_to_send - previous_value} м³ "
                f"с момента последней передачи!\n"
                f"Пожалуйста, проверьте правильность показаний."
            )
            _LOGGER.warning(warning_msg)
            await self._show_notification(warning_msg, is_error=False)
        
        # Отправляем показания
        _LOGGER.info("🚀 Отправка показаний: %s м³", value_to_send)
        result = await self.coordinator.async_send_indication(value_to_send)
        
        if result.get("success"):
            _LOGGER.info("✅ Показания успешно переданы: %s м³", value_to_send)
            await self._show_notification(f"✅ Показания {value_to_send} м³ успешно переданы!")
            # Очищаем сохраненное значение
            self.coordinator.pending_value = None
            # Обновляем данные
            await self.coordinator.async_request_refresh()
        else:
            error_msg = result.get('message', 'Неизвестная ошибка')
            _LOGGER.error("❌ Ошибка при передаче: %s", error_msg)
            await self._show_notification(f"❌ Ошибка: {error_msg}", is_error=True)
    
    async def _show_notification(self, message: str, is_error: bool = False) -> None:
        """Show notification."""
        notification_id = f"gazprom_button_{self.coordinator.entry.entry_id}"
        try:
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "❌ Ошибка" if is_error else "Газпром ЛК",
                    "message": message,
                    "notification_id": notification_id,
                },
                blocking=False,
            )
        except Exception as err:
            _LOGGER.debug("Не удалось показать уведомление: %s", err)