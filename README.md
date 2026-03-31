# ⚡ Elpriset Just Nu — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/TSA3000/ha-elprisetjustnu.svg)](https://github.com/TSA3000/ha-elprisetjustnu/releases)
[![HA min version](https://img.shields.io/badge/Home%20Assistant-%3E%3D2024.1-blue.svg)](https://www.home-assistant.io)

Real-time Swedish electricity prices (SE1–SE4) via [Elpriset Just Nu](https://www.elprisetjustnu.se/).
Supports the 15-minute price intervals introduced in Sweden in October 2025.

> *Elpriser tillhandahålls av [Elpriset just nu.se](https://www.elprisetjustnu.se)*

---

## ✨ Features

- **8 sensors:** today and tomorrow prices — current, highest, lowest, average, next
- **Selectable unit:** öre/kWh or SEK/kWh — switch anytime via Configure
- **15-minute intervals:** full 96-slot daily coverage
- **Smart attributes:** price trend, price level, tomorrow average, full price data
- **ApexCharts support:** `price_data` attribute with timestamps ready for charts
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

> To change the unit or area later, click **Configure** on the integration card.

---

## 📊 Sensors (example: SE3 device)

### Today

| Sensor | Description |
|---|---|
| Current Price | Live price in your selected unit |
| Highest Price | Daily high |
| Lowest Price | Daily low |
| Average Price | Daily average |
| Next Price | Price for the next 15-min slot |

### Tomorrow

| Sensor | Description |
|---|---|
| Highest Price Tomorrow | Tomorrow's high — available after ~13:00 CET |
| Lowest Price Tomorrow | Tomorrow's low — available after ~13:00 CET |
| Average Price Tomorrow | Tomorrow's average — available after ~13:00 CET |

> Tomorrow sensors show `unknown` until the API publishes prices each afternoon.
> They update automatically on the next 15-minute poll after becoming available.

---

## 🔖 Attributes on Current Price sensor

| Attribute | Example value | Description |
|---|---|---|
| `price_trend` | `rising` | vs next 15-min slot |
| `price_level` | `cheap` | relative to today's range |
| `next_price` | `132.5` | next slot price |
| `price_data` | `[{"start": "...", "price": 177.55}, ...]` | all slots with timestamps |
| `all_prices_today` | `[112.3, 118.1, ...]` | flat list of today's prices |
| `data_points` | `96` | number of slots fetched |
| `price_area` | `SE3` | configured area |
| `unit` | `öre/kWh` | selected unit |
| `tomorrow_available` | `true` | whether tomorrow's prices are published |
| `tomorrow_average` | `145.2` | tomorrow's average price |

---

## 📈 Dashboard Chart

Requires [ApexCharts Card](https://github.com/RomRider/apexcharts-card) from HACS.

![Electricity price chart SE3](images/apexcharts_ex01.png)

Add this to your dashboard via **Edit → Add Card → Manual**:

```yaml
type: custom:apexcharts-card
experimental:
  color_threshold: true
header:
  show: true
  title: Electricity Prices SE3
  show_states: true
  colorize_states: true
graph_span: 32h
span:
  end: day
  offset: +1d
now:
  show: true
  label: Now
  color: var(--primary-color)
apex_config:
  chart:
    height: 190px
  legend:
    showForSingleSeries: false
  plotOptions:
    bar:
      borderRadius: 0
  yaxis:
    min: 0
    decimalsInFloat: 0
    forceNiceScale: true
series:
  - entity: sensor.elpriset_just_nu_se3_current_price
    name: " "
    unit: " öre/kWh"
    type: column
    float_precision: 1
    show:
      extremas: true
      in_header: before_now
      header_color_threshold: true
    data_generator: |
      return entity.attributes.price_data.map((item) => {
        return [new Date(item["start"]).getTime(), item["price"]];
      });
    color_threshold:
      - value: 0
        color: "#8be9fd"
      - value: 100
        color: "#50fa7b"
      - value: 150
        color: "#8be978"
      - value: 200
        color: "#f8f872"
      - value: 250
        color: "#ffb86c"
      - value: 300
        color: "#ff9859"
      - value: 350
        color: "#ff7846"
      - value: 400
        color: "#ff5555"
  - entity: sensor.elpriset_just_nu_se3_current_price
    name: Lowest
    unit: " öre/kWh"
    show:
      in_chart: false
      in_header: true
    data_generator: |
      let prices = entity.attributes.price_data.map(x => x.price);
      return [[new Date().getTime(), Math.min(...prices)]];
  - entity: sensor.elpriset_just_nu_se3_current_price
    name: Highest
    unit: " öre/kWh"
    show:
      in_chart: false
      in_header: true
    data_generator: |
      let prices = entity.attributes.price_data.map(x => x.price);
      return [[new Date().getTime(), Math.max(...prices)]];
```

> Replace `sensor.elpriset_just_nu_se3_current_price` with your actual entity ID.
> Find it under **Settings → Entities → search elprisetjustnu**.

---

## 💡 Automation example

Get notified when tomorrow's prices are published:

```yaml
automation:
  - alias: "Notify when tomorrow prices are available"
    trigger:
      - platform: template
        value_template: >
          {{ state_attr('sensor.elpriset_just_nu_se3_current_price',
             'tomorrow_available') == true }}
    action:
      - service: notify.mobile_app
        data:
          message: >
            Tomorrow's average price:
            {{ state_attr('sensor.elpriset_just_nu_se3_current_price',
               'tomorrow_average') }} öre/kWh
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