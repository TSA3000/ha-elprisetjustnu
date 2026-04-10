# Release v0.2.7 — Fix Attribute Size Limit

## 🐛 Bug Fix

- **Fixed attributes exceeding HA's 16KB limit.** The `price_data` and `price_data_last_week` attributes now use the compact `[timestamp_ms, price]` array format instead of `{"start": "...", "price": ...}` objects. This reduces attribute size from ~23KB to ~9KB — well under the 16KB recorder limit.
- **Removed `all_prices_today` attribute.** This was redundant with `price_data` and contributed to the size overflow.

## ⚠️ Breaking Change for Chart Users

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

## 📋 Changed files

- `sensor.py` — Compact `[timestamp_ms, price]` format, removed `all_prices_today`
- `manifest.json` — Bumped to `0.2.7`
- `tests/test_sensor.py` — Updated for new attribute format
- `README.md` — Updated chart examples and attributes documentation
