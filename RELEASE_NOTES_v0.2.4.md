# Release v0.2.4 — Configuration Toggles

## ✨ New Features

- **Include VAT toggle.** New on/off switch to include or exclude VAT (moms) from all prices. When off, the VAT rate field is ignored and sensors show raw spot prices. Enabled by default.
- **Show unit toggle.** New on/off switch to hide the unit label (öre/kWh or SEK/kWh) from sensor values. Useful for cleaner dashboard cards where the unit is already obvious. Enabled by default.

## ⚙️ Configuration UI

The setup and Configure flows now show:

| Setting | Default | Description |
|---|---|---|
| Price area | SE3 | Swedish electricity zone |
| Unit | öre/kWh | öre/kWh or SEK/kWh |
| Include VAT (moms) | ✅ On | Apply VAT to all prices |
| VAT rate (%) | 25 | Only used when Include VAT is on |
| Show unit on sensors | ✅ On | Display unit label on sensor values |

All settings can be changed anytime via **Configure** — no need to remove the integration.

## 📋 Changed files

- `const.py` — Added `CONF_INCLUDE_VAT`, `CONF_SHOW_UNIT`
- `config_flow.py` — Added both toggles to setup and options flow
- `sensor.py` — Respects `include_vat` toggle (ignores VAT rate when off), hides unit when `show_unit` is off
- `manifest.json` — Bumped to `0.2.4`
- `strings.json` — Added labels for both toggles
- `translations/en.json` — Added English labels
- `translations/sv.json` — Added Swedish labels ("Inkludera moms", "Visa enhet på sensorer")
