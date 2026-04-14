"""Constants for the Queensland Fuel Prices integration."""

DOMAIN = "qld_fuel_prices"

# API Base URL
API_BASE_URL = "https://fppdirectapi-prod.fuelpricesqld.com.au"

# API Endpoints
ENDPOINT_SITE_DETAILS = "/Subscriber/GetFullSiteDetails"
ENDPOINT_GEO_REGIONS = "/Subscriber/GetCountryGeographicRegions"
ENDPOINT_BRANDS = "/Subscriber/GetCountryBrands"
# ENDPOINT_FUEL_TYPES = "/Subscriber/GetCountryFuelTypes"
ENDPOINT_SITE_PRICES = "/Price/GetSitesPrices"

# Australia country ID used by the FPD API
COUNTRY_ID = 21

# Geographic region level for Queensland (state level = 3, region ID = 1)
GEO_REGION_LEVEL = 3
GEO_REGION_ID = 1

# Update intervals
# Static data (sites, brands, fuel types) - once per day
STATIC_UPDATE_INTERVAL_HOURS = 24

# Fuel prices - several times per day
PRICE_UPDATE_INTERVAL_MINUTES = 30

# Config keys
CONF_API_KEY = "api_key"
CONF_FUEL_TYPES = "fuel_types"

# Storage keys
STORAGE_KEY_SITES = "sites"
STORAGE_KEY_BRANDS = "brands"
STORAGE_KEY_FUEL_TYPES = "fuel_types"

# Coordinator names
COORDINATOR_STATIC = "static"
COORDINATOR_PRICES = "prices"

# Sensor attributes
ATTR_SITE_ID = "site_id"
ATTR_SITE_NAME = "site_name"
ATTR_BRAND = "brand"
ATTR_ADDRESS = "address"
ATTR_POSTCODE = "postcode"
ATTR_LATITUDE = "latitude"
ATTR_LONGITUDE = "longitude"
ATTR_FUEL_TYPE = "fuel_type"

# Things
CREATE_ENTRY_TITLE = "Queensland Fuel Prices"

# Fuel Types
FUEL_TYPE_LOOKUP = {
    2: "Unleaded",
    3: "Diesel",
    4: "LPG",
    5: "Premium Unleaded 95",
    6: "ULSD",
    8: "Premium Unleaded 98",
    11: "LRP",
    12: "e10",
    13: "Premium e5",
    14: "Premium Diesel",
    16: "Bio-Diesel 20",
    19: "e85",
    21: "OPAL",
    22: "Compressed natural gas",
    23: "Liquefied natural gas",
}
