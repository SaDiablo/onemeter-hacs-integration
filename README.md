# OneMeter Cloud Integration for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![HACS Badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)
[![License][license-shield]](LICENSE)

This custom component integrates OneMeter Cloud smart energy meters with Home Assistant, allowing you to monitor your energy usage directly in your smart home dashboard.

## Features

- Monitor real-time energy usage from OneMeter devices
- Track positive, negative, and absolute energy consumption
- Monitor reactive energy components (R1, R4)
- View instantaneous power measurements
- View device diagnostic information (battery voltage, meter info)
- View monthly usage statistics

## Installation

### HACS (Recommended)

1. Make sure [HACS](https://hacs.xyz/) is installed in your Home Assistant instance
2. Go to HACS → Integrations
3. Click the "+" button and search for "OneMeter"
4. Select "OneMeter Cloud integration" and click "Install"
5. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/sadiablo/onemeter-hacs-integration/releases)
2. Extract the contents to your Home Assistant `custom_components` directory
3. Restart Home Assistant

## Configuration

1. Go to Home Assistant Settings → Devices & Services
2. Click "Add Integration"
3. Search for "OneMeter Cloud" and select it
4. Enter your OneMeter Cloud API key and Device ID
5. Configure update interval in the options (if needed)

## Sensors

This integration provides the following sensors:

| Sensor | Description | Unit | Category |
|--------|-------------|------|----------|
| Energy A+ (total) | Positive active energy consumption | kWh | Energy |
| Energy A- (total) | Negative active energy (production) | kWh | Energy |
| Energy R1 (total) | Reactive energy R1 component | kvarh | Energy |
| Energy R4 (total) | Reactive energy R4 component | kvarh | Energy |
| Energy \|A\| (total) | Absolute active energy total | kWh | Energy |
| Instantaneous Power | Current power usage | kW | Power |
| Battery Voltage | Device battery voltage | V | Diagnostic |
| Meter Serial Number | Meter identification number | - | Diagnostic |
| Tariff | Current energy tariff | - | Energy |
| This Month Usage | Energy consumption in current month | kWh | Energy |
| Previous Month Usage | Energy consumption in previous month | kWh | Energy |

Additional diagnostic sensors are available but disabled by default:
- Meter error code
- Physical address
- Successful readings count
- Failed readings count

## Energy Dashboard Integration

The energy sensors from this integration can be added to the Home Assistant Energy Dashboard:

1. Go to Settings → Dashboards → Energy
2. Add the OneMeter energy consumption sensor (Energy A+ total)
3. If you have solar production, add the Energy A- sensor as a grid return/solar production source

## Troubleshooting

- **No data appears**: Check if your OneMeter Cloud account is active and has connected devices
- **Authentication errors**: Verify your API key is correct
- **API errors**: Check if your device ID is correct and the device is online
- **Rate limiting**: If you experience API rate limiting, increase the update interval in the integration options

## API Documentation

This integration uses the official OneMeter Cloud API. For more information, see the [API documentation](https://cloud.onemeter.com/api).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see the [LICENSE](LICENSE) file for details.

---

[releases]: https://github.com/sadiablo/onemeter-hacs-integration/releases
[releases-shield]: https://img.shields.io/github/release/sadiablo/onemeter-hacs-integration.svg
[license-shield]: https://img.shields.io/github/license/sadiablo/onemeter-hacs-integration.svg