# Available Sensors

The OneMeter Cloud integration provides several sensors that allow you to monitor different aspects of your energy usage. Each sensor represents a different measurement from your OneMeter device.

## Energy Sensors

| Sensor | Entity ID | Description | Unit | OBIS Code |
|--------|-----------|-------------|------|-----------|
| Energy A+ (total) | `sensor.onemeter_energy_plus` | Positive active energy consumption (energy drawn from the grid) | kWh | 1.8.0 |
| Energy A- (total) | `sensor.onemeter_energy_minus` | Negative active energy (energy sent back to the grid, e.g., from solar panels) | kWh | 2.8.0 |
| Energy R1 (total) | `sensor.onemeter_energy_r1` | Reactive energy R1 component (inductive load when consuming) | kvarh | 5.8.0 |
| Energy R4 (total) | `sensor.onemeter_energy_r4` | Reactive energy R4 component (capacitive load when consuming) | kvarh | 8.8.0 |
| Energy \|A\| (total) | `sensor.onemeter_energy_abs` | Absolute active energy total (sum of consumption and production) | kWh | 15.8.0 |

## Power Sensors

| Sensor | Entity ID | Description | Unit | OBIS Code |
|--------|-----------|-------------|------|-----------|
| Instantaneous Power | `sensor.onemeter_power` | Current active power usage | kW | 16.7.0 |

## Usage Statistics

| Sensor | Entity ID | Description | Unit |
|--------|-----------|-------------|------|
| This Month Usage | `sensor.onemeter_this_month` | Energy consumption in the current month | kWh |
| Previous Month Usage | `sensor.onemeter_previous_month` | Energy consumption in the previous month | kWh |

## Tariff Information

| Sensor | Entity ID | Description | Unit | OBIS Code |
|--------|-----------|-------------|------|-----------|
| Tariff | `sensor.onemeter_tariff` | Current active energy tariff | - | 0.2.2 |

## Diagnostic Sensors

These sensors provide information about the OneMeter device itself.

| Sensor | Entity ID | Description | Unit | OBIS Code |
|--------|-----------|-------------|------|-----------|
| Battery Voltage | `sensor.onemeter_battery_voltage` | Device battery voltage | V | S.1.1.2 |
| Meter Serial Number | `sensor.onemeter_meter_serial` | Meter identification number | - | C.1.0 |
| UART Communication Parameters | `sensor.onemeter_uart_params` | UART communication parameters | - | S.1.1.8 |

## Hidden Diagnostic Sensors

These sensors are available but disabled by default. To enable them, go to Settings > Devices & Services > Entities, find the sensor, and click the "Enable" button.

| Sensor | Entity ID | Description | Unit | OBIS Code |
|--------|-----------|-------------|------|-----------|
| Meter Error | `sensor.onemeter_meter_error` | Meter error code | - | F.F.0 |
| Physical Address | `sensor.onemeter_physical_address` | Meter physical IEC address | - | C.90.1 |
| Successful Readouts | `sensor.onemeter_successful_readouts` | Count of successful meter readings | - | S.1.1.6 |
| Failed Readouts | `sensor.onemeter_failed_readouts` | Count of failed meter readings | - | S.1.1.7 |

## Notes on Sensor Availability

- Not all sensors may be available for every OneMeter device model
- Some values may be zero or null if not supported by your specific meter
- Sensor availability depends on what data is provided by the OneMeter Cloud API
- The update frequency of all sensors is determined by the configured update interval in your integration settings

For more information on how to use these sensors in automations or dashboards, see the [Usage Guide](usage.md).