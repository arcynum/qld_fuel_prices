"""Data update coordinators for Queensland Fuel Prices."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FPDApiClient, FPDApiError
from .const import DOMAIN, PRICE_UPDATE_INTERVAL_MINUTES, STATIC_UPDATE_INTERVAL_HOURS

_LOGGER = logging.getLogger(__name__)


class StaticDataCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that refreshes reference data (sites, brands, fuel types) once per day.

    This keeps API calls to a minimum for data that rarely changes.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        client: FPDApiClient,
        geo_region_level: int,
        geo_region_id: int,
    ) -> None:
        """Initialise the static data coordinator."""
        self._client = client
        self._geo_region_level = geo_region_level
        self._geo_region_id = geo_region_id

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_static",
            update_interval=timedelta(hours=STATIC_UPDATE_INTERVAL_HOURS),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch static reference data from the API."""
        try:
            brands_raw, sites_raw = await _gather(
                self._client.get_brands(),
                self._client.get_site_details(
                    self._geo_region_level, self._geo_region_id
                ),
            )
        except FPDApiError as err:
            raise UpdateFailed(f"Error fetching static data: {err}") from err

        # Index brands and fuel types by ID for easy lookup
        brands: dict[int, str] = {
            b["BrandId"]: b["Name"]
            for b in brands_raw
            if "BrandId" in b and "Name" in b
        }

        # Index sites by SiteId
        sites: dict[int, dict[str, Any]] = {}
        for site in sites_raw:
            site_id = site.get("S")  # SiteId field is "S" in the API response
            if site_id is None:
                continue
            sites[site_id] = {
                "site_id": site_id,
                "name": site.get("N", "Unknown"),  # Name
                "brand_id": site.get("B"),  # BrandId
                "brand": brands.get(site.get("B"), "Unknown"),
                "address": site.get("A", ""),  # Address
                "postcode": site.get("P", ""),  # Postcode
                "latitude": site.get("Lat"),  # Latitude
                "longitude": site.get("Lng"),  # Longitude
            }

        _LOGGER.debug(
            "Static data refreshed: %d sites, %d brands",
            len(sites),
            len(brands),
        )

        return {
            "sites": sites,
            "brands": brands,
        }


class PriceCoordinator(DataUpdateCoordinator[dict[int, dict[int, float]]]):
    """Coordinator that refreshes fuel prices multiple times per day.

    Returns a nested dict: {site_id: {fuel_type_id: price_in_cents}}
    """

    def __init__(
        self,
        hass: HomeAssistant,
        client: FPDApiClient,
        geo_region_level: int,
        geo_region_id: int,
    ) -> None:
        """Initialise the price coordinator."""
        self._client = client
        self._geo_region_level = geo_region_level
        self._geo_region_id = geo_region_id

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_prices",
            update_interval=timedelta(minutes=PRICE_UPDATE_INTERVAL_MINUTES),
        )

    async def _async_update_data(self) -> dict[int, dict[int, float]]:
        """Fetch latest fuel prices from the API."""
        try:
            raw_prices = await self._client.get_site_prices(
                self._geo_region_level, self._geo_region_id
            )
        except FPDApiError as err:
            raise UpdateFailed(f"Error fetching price data: {err}") from err

        # Build {site_id: {fuel_type_id: price}} mapping
        prices: dict[int, dict[int, float]] = {}
        for entry in raw_prices:
            site_id = entry.get("SiteId")
            fuel_id = entry.get("FuelId")
            price = entry.get("Price")
            if site_id is None or fuel_id is None or price is None:
                continue
            if site_id not in prices:
                prices[site_id] = {}
            prices[site_id][fuel_id] = round(price / 10, 1)

        _LOGGER.debug("Price data refreshed: %d sites with prices", len(prices))
        return prices


async def _gather(*coros):
    """Run coroutines concurrently."""
    return await asyncio.gather(*coros)
