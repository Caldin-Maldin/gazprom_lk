"""The Gazprom LK integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .const import DOMAIN, SERVICE_SEND_INDICATION, SERVICE_UPDATE_DATA
from .coordinator import GazpromLKDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.BUTTON, Platform.NUMBER]

SEND_INDICATION_SCHEMA = vol.Schema({
    vol.Required("value"): vol.Coerce(float),
})

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Gazprom LK from a config entry."""
    _LOGGER.info("Настройка интеграции Gazprom LK для entry: %s", entry.entry_id)
    
    coordinator = GazpromLKDataUpdateCoordinator(hass, entry)
    
    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    # Register services
    async def async_handle_send_indication(call: ServiceCall) -> None:
        """Handle send indication service."""
        value = call.data.get("value")
        _LOGGER.info("Сервис send_indication вызван со значением: %s", value)
        result = await coordinator.async_send_indication(value)
        
        if result.get("success"):
            _LOGGER.info("Показания успешно переданы через сервис: %s м³", value)
        else:
            _LOGGER.error("Ошибка при передаче показаний через сервис: %s", result.get('message'))
    
    async def async_handle_update_data(call: ServiceCall) -> None:
        """Handle update data service."""
        try:
            await coordinator.async_request_refresh()
            _LOGGER.info("Данные успешно обновлены через сервис")
        except Exception as err:
            _LOGGER.error("Ошибка при обновлении данных через сервис: %s", err)
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_INDICATION,
        async_handle_send_indication,
        schema=SEND_INDICATION_SCHEMA
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_DATA,
        async_handle_update_data,
    )
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Выгрузка интеграции Gazprom LK для entry: %s", entry.entry_id)
    
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        
        # Remove services
        hass.services.async_remove(DOMAIN, SERVICE_SEND_INDICATION)
        hass.services.async_remove(DOMAIN, SERVICE_UPDATE_DATA)
    
    return unload_ok

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Gazprom LK integration."""
    _LOGGER.debug("Глобальная настройка Gazprom LK")
    # Эта функция нужна для совместимости, но основная настройка через config_flow
    return True