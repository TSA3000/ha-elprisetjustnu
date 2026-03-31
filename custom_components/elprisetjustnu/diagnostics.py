"""Diagnostics support for Elpriset Just Nu."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data or {}
    today = data.get("today", [])
    tomorrow = data.get("tomorrow", [])

    return {
        "config_entry": {
            "entry_id": entry.entry_id,
            "data": dict(entry.data),
            "options": dict(entry.options),
        },
        "coordinator": {
            "region": coordinator.region,
            "update_interval_seconds": coordinator.update_interval.total_seconds(),
            "last_update_success": coordinator.last_update_success,
        },
        "data_summary": {
            "today_slots": len(today),
            "tomorrow_slots": len(tomorrow),
            "today_first": today[0]["time_start"] if today else None,
            "today_last": today[-1]["time_end"] if today else None,
            "tomorrow_first": tomorrow[0]["time_start"] if tomorrow else None,
            "tomorrow_last": tomorrow[-1]["time_end"] if tomorrow else None,
        },
    }
