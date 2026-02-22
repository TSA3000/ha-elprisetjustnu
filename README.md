# ⚡ Elpriset Just Nu - Home Assistant Integration

**Version:** 0.1.3 | **Last Updated:** February 22, 2026, 18:48 CET

A custom component for Home Assistant that fetches the current and upcoming electricity prices for Swedish price areas (SE1, SE2, SE3, SE4). 

This integration uses the open and free API from [Elpriset Just Nu](https://www.elprisetjustnu.se/). It automatically adapts to the 15-minute price intervals introduced in Sweden in October 2025, ensuring your Home Assistant always knows the exact current price.

*Elpriser tillhandahålls av [Elpriset just nu.se](https://www.elprisetjustnu.se)*

> **Note:** This integration was built as a test.

## ✨ Features
* **Real-time Pricing (öre/kWh):** Fetches electricity prices and automatically converts them from SEK to öre for easier everyday reading.
* **Quarter-Hourly Updates:** Fully supports the 96 daily price intervals.
* **Three Dedicated Sensors:** Instead of hiding data in attributes, this integration creates three distinct, easy-to-use sensors:
  * Current Price
  * Highest Price Today
  * Lowest Price Today
* **Device Grouping:** All sensors are neatly grouped under a single "Device" in Home Assistant to keep your setup organized.
* **UI Configuration:** Easy setup via the Home Assistant UI (Config Flow)—no YAML required!

## 📥 Installation

### Method 1: HACS (Recommended)
1. Open Home Assistant and navigate to **HACS**.
2. Click on the three dots (`⋮`) in the top right corner and select **Custom repositories**.
3. Paste the URL to this GitHub repository and select **Integration** as the category. Click **Add**.
4. Close the popup, and you should now see "Elpriset Just Nu" in your HACS pending downloads.
5. Click **Download**.
6. **Restart Home Assistant.**

### Method 2: Manual
1. Download this repository as a ZIP file.
2. Extract the ZIP and copy the `custom_components/elprisetjustnu` folder into your Home Assistant's `custom_components` directory.
3. **Restart Home Assistant.**

## ⚙️ Configuration
1. In Home Assistant, go to **Settings** -> **Devices & Services**.
2. Click **+ Add Integration** in the bottom right corner.
3. Search for **Elpriset Just Nu** and select it.
4. Choose your price area (SE1, SE2, SE3, or SE4) from the dropdown menu and click Submit.
5. Done! Your new sensors will immediately populate.

## 📊 Sensor Details

Once configured, the integration creates a single Device containing three distinct sensors. Assuming you selected **SE3**, you will get:

* `sensor.elprisetjustnu_se3_current_price` (State: Current price in öre/kWh)
* `sensor.elprisetjustnu_se3_highest_price_today` (State: Max price of the day in öre/kWh)
* `sensor.elprisetjustnu_se3_lowest_price_today` (State: Min price of the day in öre/kWh)

## 🐛 Troubleshooting
If the sensors become unavailable, check the Home Assistant logs (`Settings` -> `System` -> `Logs`). The integration relies on an external API, so occasional network timeouts may occur, but it will automatically retry on the next 15-minute update cycle.

---

## 👨‍💻 Author
**Sam Mahdi**
