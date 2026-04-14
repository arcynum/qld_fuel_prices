"""Config flow for Queensland Fuel Prices integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import FPDApiClient, FPDAuthError
from .const import CONF_API_KEY, CONF_FUEL_TYPES, CREATE_ENTRY_TITLE, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
        vol.Required(CONF_FUEL_TYPES, default=["8"]): SelectSelector(
            SelectSelectorConfig(
                options=[
                    {"value": "2", "label": "Unleaded"},
                    {"value": "3", "label": "Diesel"},
                    {"value": "4", "label": "LPG"},
                    {"value": "5", "label": "Premium Unleaded 95"},
                    {"value": "6", "label": "ULSD"},
                    {"value": "8", "label": "Premium Unleaded 98"},
                    {"value": "11", "label": "LRP"},
                    {"value": "12", "label": "e10"},
                    {"value": "13", "label": "Premium e5"},
                    {"value": "14", "label": "Premium Diesel"},
                    {"value": "16", "label": "Bio-Diesel 20"},
                    {"value": "19", "label": "e85"},
                    {"value": "21", "label": "OPAL"},
                    {"value": "22", "label": "Compressed natural gas"},
                    {"value": "23", "label": "Liquefied natural gas"},
                ],
                multiple=True,
                mode=SelectSelectorMode.LIST,
            )
        ),
    }
)


async def _validate_api_key(
    hass: HomeAssistant, data: dict[str, Any]
) -> dict[str, str]:
    """Validate the user input and return info to be stored."""
    session = async_get_clientsession(hass)
    client = FPDApiClient(api_key=data[CONF_API_KEY], session=session)

    if not await client.validate_api_key():
        raise FPDAuthError("invalid_auth")

    return data


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the configuration flow for Queensland Fuel Prices."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await _validate_api_key(self.hass, user_input)
            except FPDAuthError:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected error during config flow")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=CREATE_ENTRY_TITLE, data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
