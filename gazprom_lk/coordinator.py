"""Data update coordinator for Gazprom LK."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, UPDATE_INTERVAL
from .gazprom_api import GazPromAPI

_LOGGER = logging.getLogger(__name__)

class GazpromLKDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Gazprom LK data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        self.entry = entry
        self.api = GazPromAPI(
            async_get_clientsession(hass),
            entry.data["login"],
            entry.data["password"]
        )
        self._token = None
        
        # Убираем автообновление - передаем None в update_interval
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=None,  # Изменили с UPDATE_INTERVAL
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        try:
            # Authenticate if needed
            if not self._token:
                auth_data = await self.api.async_authenticate()
                if not auth_data["auth_status"]:
                    raise UpdateFailed(f"Authentication failed: {auth_data['auth_message']}")
                self._token = auth_data["auth_token"]
            
            # Get data
            data = await self.api.async_get_info(self._token)
            
            # Проверяем наличие ошибки в данных
            if data.get("error", "").strip():
                # Try to re-authenticate on error
                self._token = None
                auth_data = await self.api.async_authenticate()
                if auth_data["auth_status"]:
                    self._token = auth_data["auth_token"]
                    data = await self.api.async_get_info(self._token)
                else:
                    raise UpdateFailed(f"Failed to get data: {data.get('error')}")
            
            # Clear token after update
            self._token = None
            
            if not data:
                raise UpdateFailed("No data received from API")
                
            return data
            
        except Exception as err:
            self._token = None
            _LOGGER.error("Error updating Gazprom LK data: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}")

    async def async_send_indication(self, value: float) -> dict[str, Any]:
        """Send indication to API."""
        try:
            # Authenticate
            auth_data = await self.api.async_authenticate()
            if not auth_data["auth_status"]:
                return {"success": False, "message": auth_data["auth_message"]}
            
            token = auth_data["auth_token"]
            
            # Get current data to get lsid and counterid
            data = await self.api.async_get_info(token)
            
            if not data.get("lsid") or not data.get("counterid"):
                return {"success": False, "message": "No counter found"}
            
            # Send indication
            result = await self.api.async_send_indication(
                token,
                data["lsid"],
                data["counterid"],
                value
            )
            
            # Clear token
            token = None
            
            # После отправки показаний НЕ делаем автообновление
            # Пользователь сам решит, когда обновить данные
            
            return result
            
        except Exception as err:
            return {"success": False, "message": str(err)}
    
    async def async_manual_update(self) -> dict[str, Any]:
        """Manual update of data."""
        # Просто вызываем обновление данных
        await self.async_request_refresh()
        return self.data or {}
