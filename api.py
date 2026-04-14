"""FPD API client for Queensland Fuel Prices."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .const import (
    API_BASE_URL,
    COUNTRY_ID,
    ENDPOINT_BRANDS,
    ENDPOINT_GEO_REGIONS,
    ENDPOINT_SITE_DETAILS,
    ENDPOINT_SITE_PRICES,
)

_LOGGER = logging.getLogger(__name__)


class FPDApiError(Exception):
    """Raised when the FPD API returns an error."""


class FPDAuthError(FPDApiError):
    """Raised when authentication fails."""


class FPDApiClient:
    """Client for the Fuel Prices Queensland Direct API."""

    def __init__(
        self,
        api_key: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialise the API client."""
        self._api_key = api_key
        self._session = session

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"FPDAPI SubscriberToken={self._api_key}",
            "Content-Type": "application/json",
        }

    async def _get(self, endpoint: str, params: dict[str, Any]) -> Any:
        """Perform a GET request against the API."""
        url = f"{API_BASE_URL}{endpoint}"
        try:
            async with self._session.get(
                url,
                headers=self._headers(),
                params=params,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status == 401:
                    raise FPDAuthError("Invalid API key - check your subscriber token.")
                if resp.status != 200:
                    text = await resp.text()
                    raise FPDApiError(
                        f"API request to {endpoint} failed with status {resp.status}: {text}"
                    )
                return await resp.json()
        except aiohttp.ClientConnectionError as err:
            raise FPDApiError(f"Connection error reaching FPD API: {err}") from err
        except TimeoutError as err:
            raise FPDApiError("Timeout while contacting FPD API") from err

    async def get_geographic_regions(self) -> list[dict[str, Any]]:
        """Return all geographic regions for Australia."""
        data = await self._get(ENDPOINT_GEO_REGIONS, {"countryId": COUNTRY_ID})
        return data.get("GeographicRegions", [])

    async def get_brands(self) -> list[dict[str, Any]]:
        """Return all fuel brands."""
        data = await self._get(ENDPOINT_BRANDS, {"countryId": COUNTRY_ID})
        return data.get("Brands", [])

    async def get_site_details(
        self, geo_region_level: int, geo_region_id: int
    ) -> list[dict[str, Any]]:
        """Return full site details for a geographic region."""
        data = await self._get(
            ENDPOINT_SITE_DETAILS,
            {
                "countryId": COUNTRY_ID,
                "geoRegionLevel": geo_region_level,
                "geoRegionId": geo_region_id,
            },
        )
        return data.get("S", [])

    async def get_site_prices(
        self, geo_region_level: int, geo_region_id: int
    ) -> list[dict[str, Any]]:
        """Return current fuel prices for a geographic region."""
        data = await self._get(
            ENDPOINT_SITE_PRICES,
            {
                "countryId": COUNTRY_ID,
                "geoRegionLevel": geo_region_level,
                "geoRegionId": geo_region_id,
            },
        )
        return data.get("SitePrices", [])

    async def validate_api_key(self) -> bool:
        """Validate the API key by calling a lightweight endpoint."""
        try:
            await self.get_brands()
            return True
        except FPDAuthError:
            return False
