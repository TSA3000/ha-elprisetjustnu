# ⚡ Elpriset Just Nu — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/TSA3000/ha-elprisetjustnu.svg)](https://github.com/TSA3000/ha-elprisetjustnu/releases)
[![HA min version](https://img.shields.io/badge/Home%20Assistant-%3E%3D2024.1-blue.svg)](https://www.home-assistant.io)

Real-time Swedish electricity prices (SE1–SE4) via [Elpriset Just Nu](https://www.elprisetjustnu.se/).
Supports the 15-minute price intervals introduced in Sweden in October 2025.

> *Elpriser tillhandahålls av [Elpriset just nu.se](https://www.elprisetjustnu.se)*

---

## ✨ Features

- **5 sensors:** Current · Highest · Lowest · Average · Next price
- **Selectable unit:** öre/kWh or SEK/kWh — switch anytime via Configure
- **15-minute intervals:** full 96-slot daily coverage
- **Smart attributes** on Current Price: price trend, price level, all daily prices
- **Error recovery:** keeps last known values if the API is temporarily unavailable
- **Device grouping:** all sensors under one Device in Home Assistant
- **UI configuration:** no YAML required

---

## 📥 Installation via HACS

1. Open **HACS** → click ⋮ → **Custom repositories**
2. Paste `https://github.com/TSA3000/ha-elprisetjustnu` → Category: **Integration** → **Add**
3. Find **Elpriset Just Nu** → click **Download**
4. **Restart Home Assistant**

## 📥 Manual Installation

1. Download this repository as a ZIP file
2. Copy `custom_components/elprisetjustnu/` into your HA `custom_components/` directory
3. **Restart Home Assistant**

---

## ⚙️ Configuration

1. **Settings** → **Devices & Services** → **Add Integration**
2. Search for **Elpriset Just Nu**
3. Select your **price area** (SE1, SE2, SE3 or SE4)
4. Select your **unit** (öre/kWh or SEK/kWh)
5. Click **Submit**

> To change the unit later, click **Configure** on the integration card — no need to reinstall.

---

## 📊 Sensors (example: SE3 device)

| Sensor | Description |
|---|---|
| Current Price | Live price in your selected unit |
| Highest Price | Daily high |
| Lowest Price | Daily low |
| Average Price | Daily average |
| Next Price | Price for the next 15-min slot |

### Attributes on Current Price sensor

| Attribute | Example value |
|---|---|
| `price_trend` | `rising` / `falling` / `stable` |
| `price_level` | `cheap` / `normal` / `expensive` |
| `next_price` | `132.5` |
| `all_prices_today` | `[112.3, 118.1, ...]` (all 96 slots) |
| `data_points` | `96` |
| `price_area` | `SE3` |
| `unit` | `öre/kWh` |

---

## 💡 Dashboard example (Entity Badge)

The integration works great as an Entity Badge on your dashboard.
Set **Entity** to `Current Price` under the `Elpriset Just Nu (SE3)` device,
enable **State** and **Icon**, and it will display live like:

```
⚡ 177.55 öre/kWh
```

---

## 🐛 Troubleshooting

Sensors may briefly show `unavailable` before ~13:00 CET — this is normal.
Tomorrow's prices are published by the API around that time each day.
The integration retries automatically on the next 15-minute cycle.

Check **Settings → System → Logs** for any errors prefixed with `elprisetjustnu`.

---

## 👨‍💻 Author

**Sam Mahdi** ([@TSA3000](https://github.com/TSA3000))