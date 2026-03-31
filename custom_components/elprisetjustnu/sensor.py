"""Sensor platform for Elpriset Just Nu."""
import logging
from datetime import datetime, timedelta
import dateutil.parser

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
    SensorEntityDescription,
)
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
    CoordinatorEntity,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, CONF_REGION, UPDATE_INTERVAL_MINUTES

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="current_price",
        name="Current Price",
        icon="mdi:lightning-bolt",
        native_unit_of_measurement="öre/kWh",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="highest_price_today",
        name="Highest Price",
        icon="mdi:arrow-up-bold-circle-outline",
        native_unit_of_measurement="öre/kWh",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="lowest_price_today",
        name="Lowest Price",
        icon="mdi:arrow-down-bold-circle-outline",
        native_unit_of_measurement="öre/kWh",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="average_price_today",
        name="Average Price",
        icon="mdi:approximately-equal",
        native_unit_of_measurement="öre/kWh",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="next_price",
        name="Next Price",
        icon="mdi:clock-fast",
        native_unit_of_measurement="öre/kWh",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Elpriset Just Nu sensor platform."""
    region = entry.options.get(CONF_REGION, entry.data.get(CONF_REGION))
    session = async_get_clientsession(hass)

    # Keep last known good data so sensors don't go unavailable on API hiccups
    _last_known_data = {}

    async def async_update_data():
        """Fetch the latest pricing data from the API."""
        now = datetime.now()
        url = (
            f"https://www.elprisetjustnu.se/api/v1/prices/"
            f"{now.strftime('%Y')}/{now.strftime('%m')}-{now.strftime('%d')}_{region}.json"
        )

        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 404:
                    # Prices not published yet (normal before ~13:00 CET)
                    _LOGGER.debug(
                        "Elpriset API returned 404 - prices not yet available for today"
                    )
                    return _last_known_data.get("data") or []
                response.raise_for_status()
                data = await response.json()
                _last_known_data["data"] = data
                return data
        except Exception as err:
            if _last_known_data.get("data"):
                _LOGGER.warning(
                    "Elpriset API error, using last known data: %s", err
                )
                return _last_known_data["data"]
            raise UpdateFailed(f"Error communicating with Elpriset API: {err}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"elprisetjustnu_{region}_coordinator",
        update_method=async_update_data,
        update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
    )

    await coordinator.async_config_entry_first_refresh()

    entities = [
        ElprisSensor(coordinator, region, description, entry.entry_id)
        for description in SENSOR_TYPES
    ]
    async_add_entities(entities)


def _get_price_level(current: float, low: float, high: float) -> str:
    """Classify the current price as cheap, normal, or expensive."""
    if high == low:
        return "normal"
    spread = high - low
    if current <= low + spread * 0.33:
        return "cheap"
    if current >= high - spread * 0.33:
        return "expensive"
    return "normal"


class ElprisSensor(CoordinatorEntity, SensorEntity):
    """Representation of an individual Elpris Sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        region: str,
        description: SensorEntityDescription,
        entry_id: str,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self.region = region
        self._attr_unique_id = f"{entry_id}_{region.lower()}_{description.key}"
        self._attr_name = f"Elpris {region} {description.name}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=f"Elpriset Just Nu ({region})",
            manufacturer="Elpriset Just Nu",
            model="Elpris API",
            configuration_url="https://www.elprisetjustnu.se/elpris-api",
        )

    def _get_prices_in_ore(self):
        """Return all prices for today in öre/kWh."""
        if not self.coordinator.data:
            return []
        return [
            round(block["SEK_per_kWh"] * 100, 2)
            for block in self.coordinator.data
        ]

    def _get_current_block(self):
        """Return the price block matching the current time."""
        if not self.coordinator.data:
            return None
        now = datetime.now().astimezone()
        for block in self.coordinator.data:
            start = dateutil.parser.parse(block["time_start"])
            end = dateutil.parser.parse(block["time_end"])
            if start <= now < end:
                return block
        return None

    def _get_next_block(self):
        """Return the next upcoming price block."""
        if not self.coordinator.data:
            return None
        now = datetime.now().astimezone()
        future_blocks = [
            block for block in self.coordinator.data
            if dateutil.parser.parse(block["time_start"]) > now
        ]
        return future_blocks[0] if future_blocks else None

    @property
    def native_value(self):
        """Return the state of the sensor in öre/kWh."""
        prices = self._get_prices_in_ore()
        if not prices:
            return None

        key = self.entity_description.key

        if key == "highest_price_today":
            return round(max(prices), 2)

        if key == "lowest_price_today":
            return round(min(prices), 2)

        if key == "average_price_today":
            return round(sum(prices) / len(prices), 2)

        if key == "current_price":
            block = self._get_current_block()
            return round(block["SEK_per_kWh"] * 100, 2) if block else None

        if key == "next_price":
            block = self._get_next_block()
            return round(block["SEK_per_kWh"] * 100, 2) if block else None

        return None

    @property
    def extra_state_attributes(self):
        """Return extra attributes — only on the current_price sensor."""
        if self.entity_description.key != "current_price":
            return {}

        prices = self._get_prices_in_ore()
        if not prices:
            return {}

        current_block = self._get_current_block()
        next_block = self._get_next_block()

        current = round(current_block["SEK_per_kWh"] * 100, 2) if current_block else None
        next_val = round(next_block["SEK_per_kWh"] * 100, 2) if next_block else None

        trend = "unknown"
        if current is not None and next_val is not None:
            diff = next_val - current
            if diff > 1:
                trend = "rising"
            elif diff < -1:
                trend = "falling"
            else:
                trend = "stable"

        return {
            "price_area": self.region,
            "currency": "öre/kWh",
            "price_trend": trend,
            "next_price": next_val,
            "price_level": _get_price_level(current, min(prices), max(prices)) if current else None,
            "all_prices_today": prices,
            "data_points": len(prices),
        }