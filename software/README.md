# HexGrove Software Apps

This directory contains MicroPython/Tildagon app modules for HexGrove sensor hexpansions. They curently run on the badge itself but should ideally be updated to
run from the EEPROM on the hexpansion.

Useful links:
 * [Running apps on the badge](https://tildagon.badge.emfcamp.org/tildagon-apps/run-on-badge/)


## Folders

| Folder | App Name | Sensor / Purpose | Key Files |
|---|---|---|---|
| `HexGrove_Alcohol` | Hex Grove Alcohol | MQ3 alcohol vapour detector | `app.py`, `metadata.json`, `tildagon.toml` |
| `HexGrove_DS18B20` | DS18B20 | DS18B20 1-Wire temperature sensor | `app.py`, `metadata.json`, `onewire.py` |
| `HexGrove_VOC_eCO2` | Hex Grove VOC eCO2 | SGP30 VOC + eCO2 air quality sensor | `app.py`, `metadata.json`, `sgp30.py`, `tildagon.toml` |
| `HexGrove_Template` | Hex Templates | Starter/reference app for new HexGrove apps | `app.py`, `metadata.json` |

## Common Runtime Behavior

Most apps in this folder follow the same pattern:

- Scan ports `1..6` for a connected hexpansion EEPROM
- Match expected VID/PID (`0xF055` / `0x2305`)
- Initialise the sensor driver for the matching module
- Display sensor values on-screen
- Use LEDs for quick status feedback (typically green = normal, red = alert/no device)
- React to insertion/removal events using the Tildagon event bus

## Per-App Notes

### `HexGrove_Alcohol`
- Reads ADC values from an MQ3 gas/alcohol sensor.
- Uses threshold-style display/LED indication (red above threshold).
- Uses `HexpansionConfig` pin mapping and live polling.

### `HexGrove_DS18B20`
- Reads DS18B20 temperature values via 1-Wire.
- Includes local 1-Wire and DS18X20 driver implementation in `onewire.py`.
- Displays temperature in Celsius.

### `HexGrove_VOC_eCO2`
- Uses the SGP30 driver in `sgp30.py`.
- Reads and displays:
  - `tVOC` (ppb)
  - `CO2eq` (ppm)
- Performs sensor init (`get_serial_id`, `init_air_quality`) on detection.

### `HexGrove_Template`
- Minimal reference app for building additional HexGrove sensor apps.
- Contains the standard scan/detect/display loop and VID/PID matching scaffold.

## Metadata and Packaging

Depending on app maturity, folders may include:

- `metadata.json`: app display name + import path
- `tildagon.toml`: app metadata, entry class, author/license/version fields

## Developing New `HexGrove_*` Apps

Use `HexGrove_Template` as a starting point:

1. Copy `HexGrove_Template` to a new `HexGrove_<SensorName>` folder
2. Update `metadata.json` path/name
3. Add or update `tildagon.toml` as needed
4. Replace the sensor init/read logic in `app.py`
5. Keep insertion/removal event handling and scan logic consistent
