"""Constants for the Elpriset Just Nu integration."""

DOMAIN = "elprisetjustnu"
PLATFORMS = ["sensor"]

CONF_REGION = "region"
CONF_UNIT = "unit"
CONF_VAT = "vat"

REGIONS = ["SE1", "SE2", "SE3", "SE4"]
UNITS = ["öre/kWh", "SEK/kWh"]

DEFAULT_VAT = 25
UPDATE_INTERVAL_MINUTES = 15