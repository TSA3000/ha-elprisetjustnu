# ⚡ Elpriset Just Nu — Release Notes

---

## v1.0.0 — Production Ready *(April 2026)*

The integration is now stable and production-ready. This release addresses all known edge cases based on community code review feedback.

### ⚠️ Breaking Change

- **Removed "Show unit on sensors" toggle.** The unit is now always set on sensors (required by HA's `MONETARY` device class). To hide the unit label on dashboard cards, use HA's frontend entity customization instead. Existing configs with `show_unit` will be silently ignored — no action needed.

### 🐛 Bug Fixes

- **Fixed timezone date rollover for Docker/UTC users.** The coordinator now uses `Europe/Stockholm` timezone explicitly for all date calculations. Previously, HA servers running in UTC (common in Docker) would fetch the wrong day's prices between midnight and 01:00–02:00 Swedish time.
- **Fixed DST shift on last week chart overlay.** The `price_data_last_week` timestamps are now shifted using date replacement (`replace()`) instead of `timedelta(days=7)`. This preserves wall-clock time across DST transitions — e.g., 14:00 CET stays 14:00 CEST, preventing a 1-hour chart misalignment during the transition week.
- **Fixed `MONETARY` device class without unit.** Sensors now always declare their unit of measurement. Setting it to `None` via the old `show_unit` toggle could cause warnings in future HA versions.

### ✨ Improvements

- **Added proper type hints to `async_setup_entry`.** The sensor platform setup function now uses `HomeAssistant`, `ConfigEntry`, and `AddEntitiesCallback` type annotations, matching HA core conventions.
- **Added `_shift_week_dst_safe()` helper.** Dedicated function for DST-aware timestamp shifting with clear documentation.
- **New test: Swedish timezone used for date.** Verifies that at 23:30 UTC (01:30 CEST), the coordinator fetches the correct Swedish date.
- **New test: DST-safe shift preserves wall-clock time.** Verifies the `_shift_week_dst_safe` function.

### 📋 Changed files

- `coordinator.py` — `dt_util.utcnow().astimezone(SWEDISH_TZ)` for date calculations
- `sensor.py` — Type hints, `_shift_week_dst_safe()`, removed `show_unit` parameter, unit always set
- `const.py` — Removed `CONF_SHOW_UNIT`
- `config_flow.py` — Removed `show_unit` toggle from setup and options
- `strings.json` / `translations/en.json` / `translations/sv.json` — Removed `show_unit` label
- `manifest.json` — Bumped to `1.0.0`
- `tests/` — Updated for `utcnow` mock, removed `show_unit` tests, added timezone and DST tests

---

## v0.2.7 — Fix Attribute Size Limit *(April 2026)*

### 🐛 Bug Fix

- **Fixed attributes exceeding HA's 16KB limit.** The `price_data` and `price_data_last_week` attributes now use the compact `[timestamp_ms, price]` array format instead of `{"start": "...", "price": ...}` objects. This reduces attribute size from ~23KB to ~9KB — well under the 16KB recorder limit.
- **Removed `all_prices_today` attribute.** This was redundant with `price_data` and contributed to the size overflow.

### ⚠️ Breaking Change for Chart Users

If you're using the ApexCharts card, update your `data_generator` — the new format is simpler:

**Before (v0.2.6):**
```yaml
data_generator: |
  return entity.attributes.price_data.map((item) => {
    return [new Date(item["start"]).getTime(), item["price"]];
  });
```

**After (v0.2.7):**
```yaml
data_generator: |
  return entity.attributes.price_data;
```

For Lowest/Highest headers, change `x.price` to `x[1]`:
```yaml
data_generator: |
  let prices = entity.attributes.price_data.map(x => x[1]);
  return [[new Date().getTime(), Math.min(...prices)]];
```

See the README for complete updated chart configs.

### 📋 Changed files

- `sensor.py` — Compact `[timestamp_ms, price]` format, removed `all_prices_today`
- `manifest.json` — Bumped to `0.2.7`
- `tests/test_sensor.py` — Updated for new attribute format
- `README.md` — Updated chart examples and attributes documentation

---

## v0.2.6 — Last Week Price Comparison *(April 2026)*

### ✨ New Feature

- **Last week price comparison.** The integration now fetches prices from the same weekday last week and exposes them as the `price_data_last_week` attribute. Timestamps are shifted +7 days so they align perfectly when overlaid on today's chart. Data is cached per day to minimize API calls (only 2 extra requests per day).

### 📈 Mixed Chart: Today vs Last Week

Use this with ApexCharts Card to show today's prices as colored bars and last week as a subtle line overlay on a second Y-axis. See the README for the full chart config.

### 🔖 New Attribute on Current Price sensor

| Attribute | Example | Description |
|---|---|---|
| `price_data_last_week` | `[[1711839600000, 88.1], ...]` | Last week same weekday, timestamps shifted +7 days for chart alignment |

### 📋 Changed files

- `coordinator.py` — Fetches last week data (7 days ago + 6 days ago), cached per day
- `sensor.py` — Added `_last_week_today()`, `_last_week_tomorrow()` helpers, `price_data_last_week` attribute with +7 day timestamp shift
- `manifest.json` — Bumped to `0.2.6`
- `tests/` — Updated for 4-response mock pattern, added last week tests

---

## v0.2.5 — VAT Toggle & Stability Fix *(April 2026)*

### ✨ New Features

- **Include VAT toggle.** On/off switch to include or exclude VAT (moms) from all prices. When off, sensors show raw spot prices regardless of the VAT rate setting. Enabled by default.
- **Configurable VAT rate.** Set any VAT percentage (default 25%). Applied to all sensor values, attributes, and chart data when the toggle is on.

### 🐛 Bug Fix

- **Fixed invalid `state_class` for monetary sensors.** Removed `SensorStateClass.MEASUREMENT` from price sensors — HA's `MONETARY` device class only supports `total` or no state class.

### 📋 Changed files

- `const.py` — Added `CONF_INCLUDE_VAT`
- `config_flow.py` — Added VAT toggle and rate to setup and options
- `sensor.py` — Removed invalid `state_class`, added VAT toggle logic, new attributes
- `manifest.json` — Bumped to `0.2.5`
- `strings.json` / `translations/` — Added labels for VAT fields
- `tests/` — Updated for new config fields, added VAT tests

---

## v0.2.3 — VAT / Moms Support *(March 2026)*

### ✨ New Feature

- **Configurable VAT (moms).** All prices can now include VAT. Set your VAT rate (default 25%) during setup or change it anytime via **Configure**.

### 📋 Changed files

- `const.py` — Added `CONF_VAT`, `DEFAULT_VAT`
- `config_flow.py` — Added VAT number selector (0–100%) to setup and options flow
- `sensor.py` — `_convert()` applies VAT multiplier to all prices and attributes
- `manifest.json` — Bumped to `0.2.3`
- `strings.json` / `translations/` — Added VAT label

---

## v0.2.2 — Swedish Translation, Tests & CI *(March 2026)*

### 🌍 Localization

- **Added Swedish translation (`sv.json`).**

### 🧪 Testing & CI/CD

- **Added comprehensive unit test suite.** 40+ tests covering all components.
- **Added GitHub Actions CI.** Tests run on push/PR against Python 3.12 and 3.13.
- **Added automated release workflow.** Pushing a `v*` tag creates a GitHub Release.

---

## v0.2.0 — Quality & Reliability *(March 2026)*

### 🐛 Bug Fixes

- Fixed timezone handling (`dt_util.now()` instead of `datetime.now()`)
- Fixed `aiohttp` timeout (proper `ClientTimeout` object)
- Fixed stale tomorrow data after midnight
- Fixed duplicate config entries

### ✨ Improvements

- Combined today + tomorrow `price_data` attribute
- Added `diagnostics.py` for HA diagnostics support
- Narrowed exception handling
- Removed `python-dateutil` dependency

---

## v0.1.6 — Initial Release *(February 2026)*

- 3 sensors: current, highest, lowest price
- Config flow (UI-based setup)
- 15-minute interval support
- HACS compatible
