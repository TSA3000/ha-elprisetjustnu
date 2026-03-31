# Release v0.2.0 — Quality & Reliability

## ⚠️ Breaking

- **Removed `python-dateutil` dependency.** The integration now uses Python's built-in `datetime.fromisoformat()` instead. No user action required — just update normally.
- **Duplicate entries are now blocked.** If you had accidentally added the same price area twice, remove the duplicate before updating.

## 🐛 Bug Fixes

- **Fixed timezone handling.** All time comparisons now use Home Assistant's timezone-aware `dt_util.now()` instead of `datetime.now()`, preventing issues in Docker and misconfigured timezone environments.
- **Fixed `aiohttp` timeout.** The API timeout now uses a proper `ClientTimeout` object instead of a bare integer, ensuring compatibility with current `aiohttp` versions.
- **Fixed stale tomorrow data after midnight.** Previously, yesterday's "tomorrow" cache could persist after the date rolled over. The cache is now cleared at midnight so today's data is always fresh.
- **Fixed duplicate config entries.** The config flow now sets a unique ID per price area and aborts if the area is already configured.

## ✨ Improvements

- **Removed `state_class` from aggregate sensors.** Only `current_price` and `next_price` now have `SensorStateClass.MEASUREMENT`. The min/max/average sensors no longer create misleading long-term statistics in HA.
- **Added `suggested_display_precision`.** All sensors now suggest 2 decimal places in the UI, so values display cleanly without manual configuration.
- **Combined today + tomorrow `price_data`.** The `price_data` attribute on the current price sensor now includes both today's and tomorrow's slots, enabling seamless 48-hour ApexCharts graphs without extra configuration.
- **Narrowed exception handling.** API fetch errors now catch only `aiohttp.ClientError` and `asyncio.TimeoutError` instead of bare `Exception`, preventing accidental suppression of unrelated errors like `CancelledError`.
- **Added `diagnostics.py`.** You can now download debug information from **Settings → Devices & Services → Elpriset Just Nu → ⋮ → Download Diagnostics**. This makes bug reports much easier.
- **Used `PLATFORMS` constant.** Platform list is now defined once in `const.py` for easier future extension.

## 📦 Dependency Changes

- Removed: `python-dateutil` (no longer needed)

## 📋 Full file changes

- `const.py` — Added `PLATFORMS` constant
- `coordinator.py` — `dt_util.now()`, `ClientTimeout`, midnight cache reset, narrowed exceptions
- `__init__.py` — Uses `PLATFORMS` constant
- `config_flow.py` — Duplicate entry prevention via `async_set_unique_id`
- `sensor.py` — `dt_util.now()`, `fromisoformat`, removed `state_class` from aggregates, `suggested_display_precision`, combined `price_data`
- `manifest.json` — Removed `python-dateutil`, bumped to `0.2.0`
- `diagnostics.py` — New file for HA diagnostics support
