# ⚡ Elpriset Just Nu — Release Notes

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

### 🧹 Housekeeping

- Removed stray `.github/release.yaml` and `.github/tests.yaml` (duplicates of files already in `.github/workflows/`)

### 📋 Changed files

- `coordinator.py` — Fetches last week data (7 days ago + 6 days ago), cached per day
- `sensor.py` — Added `_last_week_today()`, `_last_week_tomorrow()` helpers, `price_data_last_week` attribute with +7 day timestamp shift
- `manifest.json` — Bumped to `0.2.6`
- `tests/conftest.py` — Added `SAMPLE_LAST_WEEK_TODAY`, `SAMPLE_LAST_WEEK_TOMORROW`
- `tests/test_coordinator.py` — Updated to 4-response mock pattern, added `test_last_week_cached_per_day`
- `tests/test_sensor.py` — Added `TestLastWeekData` class (3 tests)

---

## v0.2.5 — VAT Toggle, Unit Toggle & Stability Fix *(April 2026)*

### ✨ New Features

- **Include VAT toggle.** On/off switch to include or exclude VAT (moms) from all prices. When off, sensors show raw spot prices regardless of the VAT rate setting. Enabled by default.
- **Configurable VAT rate.** Set any VAT percentage (default 25%). Applied to all sensor values, attributes, and chart data when the toggle is on.
- **Show unit toggle.** On/off switch to hide the unit label (öre/kWh or SEK/kWh) from sensor values. Useful for cleaner dashboard cards. Enabled by default.

### 🐛 Bug Fix

- **Fixed invalid `state_class` for monetary sensors.** Removed `SensorStateClass.MEASUREMENT` from price sensors — HA's `MONETARY` device class only supports `total` or no state class.

### ⚙️ Configuration

All settings are available in both the initial setup and the **Configure** button:

| Setting | Default | Description |
|---|---|---|
| Price area | SE3 | SE1, SE2, SE3, or SE4 |
| Unit | öre/kWh | öre/kWh or SEK/kWh |
| Include VAT (moms) | ✅ On | Apply VAT to all prices |
| VAT rate (%) | 25 | Only applies when toggle is on |
| Show unit on sensors | ✅ On | Display unit label on sensor values |

### 🔖 New Attributes on Current Price sensor

| Attribute | Example | Description |
|---|---|---|
| `vat_percent` | `25` | Configured VAT rate |
| `includes_vat` | `true` | Whether prices include VAT |

### 📋 Changed files

- `const.py` — Added `CONF_INCLUDE_VAT`, `CONF_SHOW_UNIT`
- `config_flow.py` — Added VAT toggle, VAT rate, and show unit toggle to setup and options
- `sensor.py` — Removed invalid `state_class`, added VAT/unit toggle logic, new attributes
- `manifest.json` — Bumped to `0.2.5`
- `strings.json` / `translations/en.json` / `translations/sv.json` — Added labels for new fields
- `tests/` — Updated for new config fields, added VAT and toggle tests

---

## v0.2.3 — VAT / Moms Support *(March 2026)*

### ✨ New Feature

- **Configurable VAT (moms).** All prices can now include VAT. Set your VAT rate (default 25%) during setup or change it anytime via **Configure**. Set to 0% for raw spot prices (previous behavior).

### How it works

- The VAT percentage is applied as a multiplier to all sensor values, attributes, and chart data
- The `price_data` attribute (used by ApexCharts) also includes VAT, so charts update automatically
- New attributes on the Current Price sensor: `vat_percent` and `includes_vat`

### 📋 Changed files

- `const.py` — Added `CONF_VAT`, `DEFAULT_VAT`
- `config_flow.py` — Added VAT number selector (0–100%) to setup and options flow
- `sensor.py` — `_convert()` applies VAT multiplier to all prices and attributes
- `manifest.json` — Bumped to `0.2.3`
- `strings.json` / `translations/en.json` / `translations/sv.json` — Added VAT label

---

## v0.2.2 — Swedish Translation, Tests & CI *(March 2026)*

### 🌍 Localization

- **Added Swedish translation (`sv.json`).** The config flow and options UI are now fully localized in Swedish.

### 🧪 Testing

- **Added comprehensive unit test suite.** 40+ tests covering the coordinator, sensor platform, config flow, diagnostics, and helpers.
- **Added GitHub Actions CI workflow.** Tests run automatically on push/PR against Python 3.12 and 3.13.

### 🚀 CI/CD

- **Added automated release workflow.** Pushing a `v*` tag now automatically creates a GitHub Release with a downloadable ZIP.

### 📋 Changed files

- `translations/sv.json` — **New** — Swedish translation
- `tests/` — **New** — Full test suite (conftest, test_config_flow, test_coordinator, test_sensor, test_diagnostics)
- `.github/workflows/tests.yaml` — **New** — CI test runner
- `.github/workflows/release.yaml` — **New** — Automated release pipeline
- `pytest.ini` — **New** — Pytest configuration
- `requirements_test.txt` — **New** — Test dependencies

---

## v0.2.0 — Quality & Reliability *(March 2026)*

### ⚠️ Breaking

- **Removed `python-dateutil` dependency.** The integration now uses Python's built-in `datetime.fromisoformat()` instead. No user action required — just update normally.
- **Duplicate entries are now blocked.** If you had accidentally added the same price area twice, remove the duplicate before updating.

### 🐛 Bug Fixes

- **Fixed timezone handling.** All time comparisons now use Home Assistant's timezone-aware `dt_util.now()` instead of `datetime.now()`, preventing issues in Docker and misconfigured timezone environments.
- **Fixed `aiohttp` timeout.** The API timeout now uses a proper `ClientTimeout` object instead of a bare integer, ensuring compatibility with current `aiohttp` versions.
- **Fixed stale tomorrow data after midnight.** Previously, yesterday's "tomorrow" cache could persist after the date rolled over. The cache is now cleared at midnight so today's data is always fresh.
- **Fixed duplicate config entries.** The config flow now sets a unique ID per price area and aborts if the area is already configured.

### ✨ Improvements

- **Removed `state_class` from aggregate sensors.** Only `current_price` and `next_price` originally had `SensorStateClass.MEASUREMENT`. The min/max/average sensors no longer create misleading long-term statistics in HA.
- **Added `suggested_display_precision`.** All sensors suggest 2 decimal places in the UI, so values display cleanly without manual configuration.
- **Combined today + tomorrow `price_data`.** The `price_data` attribute on the current price sensor includes both today's and tomorrow's slots, enabling seamless 48-hour ApexCharts graphs.
- **Narrowed exception handling.** API fetch errors now catch only `aiohttp.ClientError` and `asyncio.TimeoutError` instead of bare `Exception`, preventing accidental suppression of unrelated errors.
- **Added `diagnostics.py`.** Download debug information from **Settings → Devices & Services → Elpriset Just Nu → ⋮ → Download Diagnostics**.
- **Used `PLATFORMS` constant.** Platform list is now defined once in `const.py` for easier future extension.

### 📦 Dependency Changes

- Removed: `python-dateutil` (no longer needed)

### 📋 Changed files

- `const.py` — Added `PLATFORMS` constant
- `coordinator.py` — `dt_util.now()`, `ClientTimeout`, midnight cache reset, narrowed exceptions
- `__init__.py` — Uses `PLATFORMS` constant
- `config_flow.py` — Duplicate entry prevention via `async_set_unique_id`
- `sensor.py` — `dt_util.now()`, `fromisoformat`, removed `state_class` from aggregates, `suggested_display_precision`, combined `price_data`
- `manifest.json` — Removed `python-dateutil`, bumped to `0.2.0`
- `diagnostics.py` — **New** — HA diagnostics support

---

## v0.1.6 — Compliance & Stability *(February 2026)*

Initial public release with core functionality:

- **3 sensors:** Current price, highest price today, lowest price today
- **Config flow:** UI-based setup — no YAML required
- **15-minute intervals:** Full 96-slot daily coverage matching Sweden's October 2025 change
- **Device grouping:** All sensors under one Device in HA
- **Unit selection:** öre/kWh or SEK/kWh
- **Error recovery:** Keeps last known values if the API is temporarily unavailable
- **HACS compatible:** Custom repository installation supported
