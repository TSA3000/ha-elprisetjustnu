# ⚡ Elpriset Just Nu — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/TSA3000/ha-elprisetjustnu.svg)](https://github.com/TSA3000/ha-elprisetjustnu/releases)
[![HA min version](https://img.shields.io/badge/Home%20Assistant-%3E%3D2024.1-blue.svg)](https://www.home-assistant.io)

Real-time Swedish electricity prices (SE1–SE4) via [Elpriset Just Nu](https://www.elprisetjustnu.se/).  
Supports the 15-minute price intervals introduced in Sweden in October 2025.

> *Elpriser tillhandahålls av [Elpriset just nu.se](https://www.elprisetjustnu.se)*

## ✨ Features

- **Real-time Pricing (öre/kWh):** Current, highest, lowest and average price
- **Quarter-Hourly Updates:** Full 96 daily price interval support
- **Three Sensors:** Current · Highest · Lowest price today
- **Device Grouping:** All sensors under one Device in Home Assistant
- **UI Configuration:** No YAML required

## 📥 Installation via HACS

1. Open **HACS** → click ⋮ → **Custom repositories**
2. Paste `https://github.com/TSA3000/ha-elprisetjustnu` → Category: **Integration** → **Add**
3. Find **Elpriset Just Nu** → click **Download**
4. **Restart Home Assistant**

## 📥 Manual Installation

1. Download this repository as a ZIP file
2. Copy `custom_components/elprisetjustnu/` into your HA `custom_components/` directory
3. **Restart Home Assistant**

## ⚙️ Configuration

1. **Settings** → **Devices & Services** → **Add Integration**
2. Search for **Elpriset Just Nu**
3. Select your price area (SE1, SE2, SE3 or SE4) → **Submit**

## 📊 Sensors (example: SE3)

| Entity | Description |
|---|---|
| `sensor.elprisetjustnu_se3_current_price` | Current price in öre/kWh |
| `sensor.elprisetjustnu_se3_highest_price_today` | Daily high in öre/kWh |
| `sensor.elprisetjustnu_se3_lowest_price_today` | Daily low in öre/kWh |

## 🐛 Troubleshooting

Sensors may briefly show `unavailable` before ~13:00 CET — this is normal.  
Tomorrow's prices are published by the API around that time each day.  
The integration retries automatically on the next 15-minute cycle.

Check **Settings → System → Logs** for any errors prefixed with `elprisetjustnu`.

## 👨‍💻 Author

**Sam Mahdi** ([@TSA3000](https://github.com/TSA3000))