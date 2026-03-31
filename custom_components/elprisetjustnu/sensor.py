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

from .const import DOMAIN, CONF_REGION
from .coordinator import ElprisetCoordinator

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
    coordinator: ElprisetCoordinator = hass.data[DOMAIN][entry.entry_id]
    region = entry.options.get(CONF_REGION, entry.data.get(CONF_REGION))

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
        coordinator: ElprisetCoordinator,
        region: str,
        description: SensorEntityDescription,
        entry_id: str,
    ):
        super().__init__(coordinator)
        self.entity_description = description
        self.region = region
        self._attr_unique_id = f"{entry_id}_{region.lower()}_{description.key}"
        self._attr_has_entity_name = True
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=f"Elpriset Just Nu ({region})",
            manufacturer="Elpriset Just Nu",
            model="Elpris API",
            configuration_url="https://www.elprisetjustnu.se/elpris-api",
        )

    def _prices_in_ore(self) -> list[float]:
        if not self.coordinator.data:
            return []
        return [round(b["SEK_per_kWh"] * 100, 2) for b in self.coordinator.data]

    def _current_block(self):
        if not self.coordinator.data:
            return None
        now = datetime.now().astimezone()
        for block in self.coordinator.data:
            start = dateutil.parser.parse(block["time_start"])
            end = dateutil.parser.parse(block["time_end"])
            if start <= now < end:
                return block
        return None

    def _next_block(self):
        if not self.coordinator.data:
            return None
        now = datetime.now().astimezone()
        future = [
            b for b in self.coordinator.data
            if dateutil.parser.parse(b["time_start"]) > now
        ]
        return future[0] if future else None

    @property
    def native_value(self):
        prices = self._prices_in_ore()
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
            block = self._current_block()
            return round(block["SEK_per_kWh"] * 100, 2) if block else None
        if key == "next_price":
            block = self._next_block()
            return round(block["SEK_per_kWh"] * 100, 2) if block else None
        return None

    @property
    def extra_state_attributes(self):
        if self.entity_description.key != "current_price":
            return {}
        prices = self._prices_in_ore()
        if not prices:
            return {}
        current_block = self._current_block()
        next_block = self._next_block()
        current = round(current_block["SEK_per_kWh"] * 100, 2) if current_block else None
        next_val = round(next_block["SEK_per_kWh"] * 100, 2) if next_block else None
        trend = "unknown"
        if current is not None and next_val is not None:
            diff = next_val - current
            trend = "rising" if diff > 1 else "falling" if diff < -1 else "stable"
        return {
            "price_area": self.region,
            "currency": "öre/kWh",
            "price_trend": trend,
            "next_price": next_val,
            "price_level": _get_price_level(current, min(prices), max(prices)) if current else None,
            "all_prices_today": prices,
            "data_points": len(prices),
        }