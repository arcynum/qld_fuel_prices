"""Queensland Fuel Prices integration for Home Assistant."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import FPDApiClient
from .const import (
    CONF_API_KEY,
    COORDINATOR_PRICES,
    COORDINATOR_STATIC,
    DOMAIN,
    GEO_REGION_ID,
    GEO_REGION_LEVEL,
)
from .coordinator import PriceCoordinator, StaticDataCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Queensland Fuel Prices from a config entry."""
    api_key = entry.data[CONF_API_KEY]

    session = async_get_clientsession(hass)
    client = FPDApiClient(api_key=api_key, session=session)

    static_coordinator = StaticDataCoordinator(
        hass=hass,
        client=client,
        geo_region_level=GEO_REGION_LEVEL,
        geo_region_id=GEO_REGION_ID,
    )

    price_coordinator = PriceCoordinator(
        hass=hass,
        client=client,
        geo_region_level=GEO_REGION_LEVEL,
        geo_region_id=GEO_REGION_ID,
    )

    # Fetch initial data – raises ConfigEntryNotReady on failure
    await static_coordinator.async_config_entry_first_refresh()
    await price_coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        COORDINATOR_STATIC: static_coordinator,
        COORDINATOR_PRICES: price_coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
