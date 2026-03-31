"""Sensor platform for Elpriset Just Nu."""

import logging
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, CONF_REGION, CONF_UNIT
from .coordinator import ElprisetCoordinator

_LOGGER = logging.getLogger(__name__)


SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    # --- Today ---
    SensorEntityDescription(
        key="current_price",
        name="Current Price",
        icon="mdi:lightning-bolt",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="highest_price_today",
        name="Highest Price",
        icon="mdi:arrow-up-bold-circle-outline",
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="lowest_price_today",
        name="Lowest Price",
        icon="mdi:arrow-down-bold-circle-outline",
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="average_price_today",
        name="Average Price",
        icon="mdi:approximately-equal",
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="next_price",
        name="Next Price",
        icon="mdi:clock-fast",
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=2,
    ),
    # --- Tomorrow ---
    SensorEntityDescription(
        key="highest_price_tomorrow",
        name="Highest Price Tomorrow",
        icon="mdi:arrow-up-bold-circle",
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="lowest_price_tomorrow",
        name="Lowest Price Tomorrow",
        icon="mdi:arrow-down-bold-circle",
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="average_price_tomorrow",
        name="Average Price Tomorrow",
        icon="mdi:approximately-equal-box",
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=2,
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


def _find_block(blocks: list, predicate):
    """Return the first block matching predicate, or None."""
    for block in blocks:
        start = datetime.fromisoformat(block["time_start"])
        end = datetime.fromisoformat(block["time_end"])
        if predicate(start, end):
            return block
    return None


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

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

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
        now = dt_util.now()
        return _find_block(self._today(), lambda s, e: s <= now < e)

    def _next_block(self):
        now = dt_util.now()
        return _find_block(self._today(), lambda s, _e: s > now)

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    @property
    def native_value(self):
        """Return the sensor value."""
        key = self.entity_description.key

        # --- Today sensors ---
        today = self._today()
        if key in (
            "current_price",
            "highest_price_today",
            "lowest_price_today",
            "average_price_today",
            "next_price",
        ):
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

        # --- Tomorrow sensors (None / unknown until API publishes) ---
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

    # ------------------------------------------------------------------
    # Attributes (only on the current_price sensor)
    # ------------------------------------------------------------------

    @property
    def extra_state_attributes(self):
        """Return rich attributes for the current price sensor."""
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

        # Trend detection
        trend = "unknown"
        if current is not None and next_val is not None:
            threshold = 1 if self._unit == "öre/kWh" else 0.01
            diff = next_val - current
            if diff > threshold:
                trend = "rising"
            elif diff < -threshold:
                trend = "falling"
            else:
                trend = "stable"

        tomorrow = self._tomorrow()
        tomorrow_prices = self._prices_converted(tomorrow) if tomorrow else []

        # Combined today + tomorrow price_data for seamless ApexCharts spanning
        combined_blocks = today + tomorrow
        price_data = [
            {
                "start": b["time_start"],
                "price": _convert(b["SEK_per_kWh"], self._unit),
            }
            for b in combined_blocks
        ]

        return {
            "price_area": self.region,
            "unit": self._unit,
            "price_trend": trend,
            "next_price": next_val,
            "price_level": (
                _get_price_level(current, min(prices), max(prices))
                if current is not None
                else None
            ),
            "all_prices_today": prices,
            "data_points": len(prices),
            "price_data": price_data,
            "tomorrow_available": len(tomorrow_prices) > 0,
            "tomorrow_average": (
                round(sum(tomorrow_prices) / len(tomorrow_prices), 2)
                if tomorrow_prices
                else None
            ),
        }
