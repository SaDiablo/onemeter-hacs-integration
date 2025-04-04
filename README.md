# OneMeter Cloud Integration for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![HACS Badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)
[![License][license-shield]](LICENSE)

This custom component integrates OneMeter Cloud smart energy meters with Home Assistant.

## Features

- Monitor real-time energy usage
- Track power, voltage, and current
- Easily connect to your OneMeter Cloud account

## Installation

### HACS (Recommended)

1. Make sure [HACS](https://hacs.xyz/) is installed in your Home Assistant instance
2. Go to HACS → Integrations
3. Click the "+" button and search for "OneMeter"
4. Select "OneMeter Cloud integration" and click "Install"
5. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/OneMeterCom/hacs-integration/releases)
2. Extract the contents to your Home Assistant `custom_components` directory
3. Restart Home Assistant

## Configuration

1. Go to Home Assistant Settings → Devices & Services
2. Click "Add Integration"
3. Search for "OneMeter Cloud" and select it
4. Enter your OneMeter Cloud account credentials
5. Optional: Provide your API key if you have one

## Sensors

This integration provides the following sensors:

- **Energy**: Total energy consumption (kWh)
- **Power**: Current power usage (W)
- **Voltage**: Current voltage (V)
- **Current**: Current amperage (A)

## Troubleshooting

- **No data appears**: Check if your OneMeter Cloud account is active and has connected devices
- **Authentication errors**: Verify your username and password
- **API errors**: Contact OneMeter support if your API key is not working

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see the [LICENSE](LICENSE) file for details.

---

[releases]: https://github.com/OneMeterCom/hacs-integration/releases
[releases-shield]: https://img.shields.io/github/release/OneMeterCom/hacs-integration.svg
[license-shield]: https://img.shields.io/github/license/OneMeterCom/hacs-integration.svg