"""Sensor platform for Elpriset Just Nu."""
import logging
from datetime import datetime
import dateutil.parser

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
    SensorEntityDescription,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, CONF_REGION, CONF_UNIT
from .coordinator import ElprisetCoordinator

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    # Today
    SensorEntityDescription(
        key="current_price",
        name="Current Price",
        icon="mdi:lightning-bolt",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="highest_price_today",
        name="Highest Price",
        icon="mdi:arrow-up-bold-circle-outline",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="lowest_price_today",
        name="Lowest Price",
        icon="mdi:arrow-down-bold-circle-outline",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="average_price_today",
        name="Average Price",
        icon="mdi:approximately-equal",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="next_price",
        name="Next Price",
        icon="mdi:clock-fast",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Tomorrow
    SensorEntityDescription(
        key="highest_price_tomorrow",
        name="Highest Price Tomorrow",
        icon="mdi:arrow-up-bold-circle",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="lowest_price_tomorrow",
        name="Lowest Price Tomorrow",
        icon="mdi:arrow-down-bold-circle",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="average_price_tomorrow",
        name="Average Price Tomorrow",
        icon="mdi:approximately-equal-box",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Elpriset Just Nu sensor platform."""
    coordinator: ElprisetCoordinator = hass.data[DOMAIN][entry.entry_id]
    region = entry.options.get(CONF_REGION, entry.data.get(CONF_REGION))
    unit = entry.options.get(CONF_UNIT, entry.data.get(CONF_UNIT, "öre/kWh"))

    entities = [
        ElprisSensor(coordinator, region, unit, description, entry.entry_id)
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


def _convert(sek_per_kwh: float, unit: str) -> float:
    """Convert SEK/kWh to the selected unit."""
    if unit == "öre/kWh":
        return round(sek_per_kwh * 100, 2)
    return round(sek_per_kwh, 4)


class ElprisSensor(CoordinatorEntity, SensorEntity):
    """Representation of an individual Elpris Sensor."""

    def __init__(
        self,
        coordinator: ElprisetCoordinator,
        region: str,
        unit: str,
        description: SensorEntityDescription,
        entry_id: str,
    ):
        super().__init__(coordinator)
        self.entity_description = description
        self.region = region
        self._unit = unit
        self._attr_unique_id = f"{entry_id}_{region.lower()}_{description.key}"
        self._attr_has_entity_name = True
        self._attr_native_unit_of_measurement = unit
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=f"Elpriset Just Nu ({region})",
            manufacturer="Elpriset Just Nu",
            model="Elpris API",
            configuration_url="https://www.elprisetjustnu.se/elpris-api",
        )

    def _today(self) -> list:
        if not self.coordinator.data:
            return []
        return self.coordinator.data.get("today", [])

    def _tomorrow(self) -> list:
        if not self.coordinator.data:
            return []
        return self.coordinator.data.get("tomorrow", [])

    def _prices_converted(self, data: list) -> list[float]:
        return [_convert(b["SEK_per_kWh"], self._unit) for b in data]

    def _current_block(self):
        now = datetime.now().astimezone()
        for block in self._today():
            start = dateutil.parser.parse(block["time_start"])
            end = dateutil.parser.parse(block["time_end"])
            if start <= now < end:
                return block
        return None

    def _next_block(self):
        now = datetime.now().astimezone()
        future = [
            b for b in self._today()
            if dateutil.parser.parse(b["time_start"]) > now
        ]
        return future[0] if future else None

    @property
    def native_value(self):
        key = self.entity_description.key

        # Today sensors
        today = self._today()
        if key in ("current_price", "highest_price_today",
                   "lowest_price_today", "average_price_today", "next_price"):
            prices = self._prices_converted(today)
            if not prices:
                return None
            if key == "highest_price_today":
                return round(max(prices), 4)
            if key == "lowest_price_today":
                return round(min(prices), 4)
            if key == "average_price_today":
                return round(sum(prices) / len(prices), 4)
            if key == "current_price":
                block = self._current_block()
                return _convert(block["SEK_per_kWh"], self._unit) if block else None
            if key == "next_price":
                block = self._next_block()
                return _convert(block["SEK_per_kWh"], self._unit) if block else None

        # Tomorrow sensors — return None (shows as unknown) until API publishes
        tomorrow = self._tomorrow()
        if not tomorrow:
            return None
        prices = self._prices_converted(tomorrow)
        if key == "highest_price_tomorrow":
            return round(max(prices), 4)
        if key == "lowest_price_tomorrow":
            return round(min(prices), 4)
        if key == "average_price_tomorrow":
            return round(sum(prices) / len(prices), 4)

        return None

    @property
    def extra_state_attributes(self):
        if self.entity_description.key != "current_price":
            return {}
        today = self._today()
        if not today:
            return {}
        prices = self._prices_converted(today)
        current_block = self._current_block()
        next_block = self._next_block()
        current = _convert(current_block["SEK_per_kWh"], self._unit) if current_block else None
        next_val = _convert(next_block["SEK_per_kWh"], self._unit) if next_block else None
        trend = "unknown"
        if current is not None and next_val is not None:
            threshold = 1 if self._unit == "öre/kWh" else 0.01
            diff = next_val - current
            trend = "rising" if diff > threshold else "falling" if diff < -threshold else "stable"

        tomorrow = self._tomorrow()
        tomorrow_prices = self._prices_converted(tomorrow) if tomorrow else []

        return {
            "price_area": self.region,
            "unit": self._unit,
            "price_trend": trend,
            "next_price": next_val,
            "price_level": _get_price_level(current, min(prices), max(prices)) if current else None,
            "all_prices_today": prices,
            "data_points": len(prices),
            "price_data": [
                {
                    "start": b["time_start"],
                    "price": _convert(b["SEK_per_kWh"], self._unit),
                }
                for b in today
            ],
            "tomorrow_available": len(tomorrow_prices) > 0,
            "tomorrow_average": round(sum(tomorrow_prices) / len(tomorrow_prices), 2)
                if tomorrow_prices else None,
        }