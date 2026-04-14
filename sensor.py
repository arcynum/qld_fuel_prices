"""Sensor platform for Queensland Fuel Prices."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_ADDRESS,
    ATTR_BRAND,
    ATTR_FUEL_TYPE,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    ATTR_POSTCODE,
    ATTR_SITE_ID,
    ATTR_SITE_NAME,
    CONF_FUEL_TYPES,
    COORDINATOR_PRICES,
    COORDINATOR_STATIC,
    DOMAIN,
    FUEL_TYPE_LOOKUP,
)
from .coordinator import PriceCoordinator, StaticDataCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Queensland Fuel Price sensors."""
    coordinators = hass.data[DOMAIN][entry.entry_id]
    static_coordinator: StaticDataCoordinator = coordinators[COORDINATOR_STATIC]
    price_coordinator: PriceCoordinator = coordinators[COORDINATOR_PRICES]

    # Track which sensors have already been created so we don't duplicate
    known_sensors: set[str] = set()

    @callback
    def _async_add_new_sensors() -> None:
        """Add sensors for any new site+fuel_type pairs discovered."""
        static_data = static_coordinator.data
        price_data = price_coordinator.data

        if not static_data or not price_data:
            return

        sites: dict = static_data.get("sites", {})
        selected_fuel_ids = {int(f) for f in entry.data.get(CONF_FUEL_TYPES, [])}
        new_entities: list[FuelPriceSensor] = []

        for site_id, site_fuel_prices in price_data.items():
            site = sites.get(site_id)
            if site is None:
                continue
            for fuel_id in site_fuel_prices:
                if fuel_id not in selected_fuel_ids:
                    continue
                fuel_name = FUEL_TYPE_LOOKUP.get(fuel_id, f"Fuel {fuel_id}")
                _LOGGER.debug("Fuel id %d and name %s", fuel_id, fuel_name)
                unique_id = f"{entry.entry_id}_{site_id}_{fuel_id}"
                if unique_id in known_sensors:
                    continue
                known_sensors.add(unique_id)
                new_entities.append(
                    FuelPriceSensor(
                        static_coordinator=static_coordinator,
                        price_coordinator=price_coordinator,
                        site_id=site_id,
                        fuel_id=fuel_id,
                        fuel_name=fuel_name,
                        entry_id=entry.entry_id,
                        unique_id=unique_id,
                    )
                )

        if new_entities:
            _LOGGER.debug("Adding %d new fuel price sensors", len(new_entities))
            async_add_entities(new_entities)

    # Create sensors on initial load and whenever static data refreshes (once/day)
    static_coordinator.async_add_listener(_async_add_new_sensors)
    _async_add_new_sensors()


def _make_device_info(site: dict[str, Any], entry_id: str) -> DeviceInfo:
    """Build a DeviceInfo for a fuel station."""
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry_id}_{site['site_id']}")},
        name=site["name"],
        manufacturer=site.get("brand", "Unknown"),
        model="Fuel Station",
        configuration_url=None,
    )


class FuelPriceSensor(CoordinatorEntity[PriceCoordinator], SensorEntity):
    """Sensor representing the price of a specific fuel at a specific station.

    Static data (name, location) comes from StaticDataCoordinator.
    The price value is updated by PriceCoordinator every 30 minutes.
    """

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "c/L"
    _attr_icon = "mdi:gas-station"

    def __init__(
        self,
        static_coordinator: StaticDataCoordinator,
        price_coordinator: PriceCoordinator,
        site_id: int,
        fuel_id: int,
        fuel_name: str,
        entry_id: str,
        unique_id: str,
    ) -> None:
        """Initialise the fuel price sensor."""
        super().__init__(price_coordinator)
        self._static_coordinator = static_coordinator
        self._site_id = site_id
        self._fuel_id = fuel_id
        self._fuel_name = fuel_name
        self._entry_id = entry_id

        self._attr_unique_id = unique_id

    def _site_data(self) -> dict[str, Any] | None:
        """Return the current site metadata from the static coordinator."""
        if not self._static_coordinator.data:
            return None
        return self._static_coordinator.data.get("sites", {}).get(self._site_id)

    # Replace with these two properties
    @property
    def name(self) -> str:
        """Return the current device name."""
        site = self._site_data()
        if site is None:
            return f"Unknown Site {self._site_id} - {self._fuel_name}"
        return f"{site.get('name', f'Site {self._site_id}')} - {self._fuel_name}"

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return the current device info."""
        site = self._site_data()
        if site is None:
            return None
        return _make_device_info(site, self._entry_id)

    @property
    def native_value(self) -> float | None:
        """Return the current price in cents per litre."""
        if not self.coordinator.data:
            return None
        site_prices = self.coordinator.data.get(self._site_id, {})
        return site_prices.get(self._fuel_id)

    @property
    def available(self) -> bool:
        """Return True if both coordinators have data and a price is available."""
        if not super().available:
            return False
        if not self._static_coordinator.last_update_success:
            return False
        return self.native_value is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes for the sensor."""
        site = self._site_data()
        attrs: dict[str, Any] = {
            ATTR_SITE_ID: self._site_id,
            ATTR_FUEL_TYPE: self._fuel_name,
        }
        if site:
            attrs.update(
                {
                    ATTR_SITE_NAME: site.get("name"),
                    ATTR_BRAND: site.get("brand"),
                    ATTR_ADDRESS: site.get("address"),
                    ATTR_POSTCODE: site.get("postcode"),
                    ATTR_LATITUDE: site.get("latitude"),
                    ATTR_LONGITUDE: site.get("longitude"),
                }
            )

        return attrs

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update entity state when the price coordinator refreshes."""
        super()._handle_coordinator_update()
