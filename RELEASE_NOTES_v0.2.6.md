# Release v0.2.6 — Last Week Price Comparison

## ✨ New Feature

- **Last week price comparison.** The integration now fetches prices from the same weekday last week and exposes them as the `price_data_last_week` attribute. Timestamps are shifted +7 days so they align perfectly when overlaid on today's chart. Data is cached per day to minimize API calls (only 2 extra requests per day).

## 📈 Mixed Chart: Today vs Last Week

Use this with ApexCharts Card to show today's prices as colored bars and last week as a subtle line overlay on a second Y-axis. See the README for the full chart config.

## 🔖 New Attribute on Current Price sensor

| Attribute | Example | Description |
|---|---|---|
| `price_data_last_week` | `[{"start": "...", "price": 95.2}, ...]` | Last week same weekday, timestamps shifted +7 days for chart alignment |

## 🧹 Housekeeping

- Removed stray `.github/release.yaml` and `.github/tests.yaml` (duplicates of files already in `.github/workflows/`)

## 📋 Changed files

- `coordinator.py` — Fetches last week data (7 days ago + 6 days ago), cached per day
- `sensor.py` — Added `_last_week_today()`, `_last_week_tomorrow()` helpers, `price_data_last_week` attribute with +7 day timestamp shift
- `manifest.json` — Bumped to `0.2.6`
- `tests/conftest.py` — Added `SAMPLE_LAST_WEEK_TODAY`, `SAMPLE_LAST_WEEK_TOMORROW`
- `tests/test_coordinator.py` — Updated to 4-response mock pattern, added `test_last_week_cached_per_day`
- `tests/test_sensor.py` — Added `TestLastWeekData` class (3 tests)
