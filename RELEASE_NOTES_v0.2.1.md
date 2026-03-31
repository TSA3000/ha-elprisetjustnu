# Release v0.2.1 — Quality & Reliability

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

## 🌍 Localization

- **Added Swedish translation (`sv.json`).** The config flow and options UI are now fully localized in Swedish.

## 🧪 Testing

- **Added comprehensive unit test suite.** 40+ tests covering the coordinator, sensor platform, config flow, diagnostics, and helpers.
- **Added GitHub Actions CI workflow.** Tests run automatically on push/PR against Python 3.12 and 3.13.

## 🚀 CI/CD

- **Added automated release workflow.** Pushing a `v*` tag now automatically creates a GitHub Release with a downloadable ZIP.

## 📦 Dependency Changes

- Removed: `python-dateutil` (no longer needed)
- Added (dev only): `pytest`, `pytest-asyncio`, `pytest-homeassistant-custom-component`

## 📋 Full file changes

- `const.py` — Added `PLATFORMS` constant
- `coordinator.py` — `dt_util.now()`, `ClientTimeout`, midnight cache reset, narrowed exceptions
- `__init__.py` — Uses `PLATFORMS` constant
- `config_flow.py` — Duplicate entry prevention via `async_set_unique_id`
- `sensor.py` — `dt_util.now()`, `fromisoformat`, removed `state_class` from aggregates, `suggested_display_precision`, combined `price_data`
- `manifest.json` — Removed `python-dateutil`, bumped to `0.2.1`
- `diagnostics.py` — **New** — HA diagnostics support
- `translations/sv.json` — **New** — Swedish translation
- `tests/` — **New** — Full test suite
- `.github/workflows/tests.yaml` — **New** — CI test runner
- `.github/workflows/release.yaml` — **New** — Automated release pipeline
- `pytest.ini` — **New** — Pytest configuration
- `requirements_test.txt` — **New** — Test dependencies
