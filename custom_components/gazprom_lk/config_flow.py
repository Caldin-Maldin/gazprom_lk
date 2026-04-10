"""Config flow for Gazprom LK."""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_LOGIN, CONF_PASSWORD
from .gazprom_api import GazPromAPI

_LOGGER = logging.getLogger(__name__)

class GazpromLKConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Gazprom LK."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                # Validate credentials
                session = async_get_clientsession(self.hass)
                api = GazPromAPI(
                    session,
                    user_input[CONF_LOGIN],
                    user_input[CONF_PASSWORD]
                )
                
                # Try to authenticate
                auth_data = await api.async_authenticate()
                
                if auth_data["auth_status"]:
                    # Get account info to verify LS number
                    lk_data = await api.async_get_info(auth_data["auth_token"])
                    
                    # Check if already configured
                    await self.async_set_unique_id(lk_data['ls_number'])
                    self._abort_if_unique_id_configured()
                    
                    return self.async_create_entry(
                        title=f"Лицевой счет: {lk_data['ls_number']}",
                        data=user_input
                    )
                else:
                    errors["base"] = "invalid_auth"
                    
            except Exception as ex:
                _LOGGER.exception("Unexpected exception: %s", ex)
                errors["base"] = "unknown"

        data_schema = vol.Schema({
            vol.Required(CONF_LOGIN): str,
            vol.Required(CONF_PASSWORD): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    # Убираем options flow, так как автообновление отключено
    # @staticmethod
    # @callback
    # def async_get_options_flow(config_entry):
    #     return GazpromLKOptionsFlow(config_entry)