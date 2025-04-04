# Usage Guide

This guide provides examples of how to use the OneMeter Cloud integration with various Home Assistant features.

## Entity Naming

When you add a OneMeter device to Home Assistant, the integration creates sensor entities with names that follow this pattern:

```
sensor.device_name_measurement_type
```

For example, if you named your device "Main House", the energy consumption sensor would be `sensor.main_house_energy_plus`.

If you provided a custom name during setup, that name will be used for the entity. Otherwise, the integration uses either the device name from the OneMeter Cloud or a default name based on the device ID.

## Energy Dashboard Integration

The OneMeter integration works seamlessly with Home Assistant's built-in Energy Dashboard to help you monitor and visualize your energy consumption.

### Setting Up the Energy Dashboard

1. Navigate to **Settings** → **Dashboards** → **Energy**
2. In the **Grid Consumption** section, click **Add Consumption**
3. Select your OneMeter energy consumption sensor (e.g., `sensor.onemeter_energy_plus`)
4. If you have solar production (energy returned to grid), click **Add Return** and select the corresponding sensor (e.g., `sensor.onemeter_energy_minus`)
5. Click **Save**

Home Assistant will now start collecting energy data for visualization in the Energy Dashboard.

## Creating Custom Cards

### Simple Energy Gauge

You can create a simple gauge to display current power usage:

```yaml
type: gauge
entity: sensor.onemeter_power
name: Current Power Usage
min: 0
max: 10
severity:
  green: 0
  yellow: 3
  red: 7
```

### Energy Statistics Card

A statistics card showing daily usage:

```yaml
type: statistics-graph
entities:
  - entity: sensor.onemeter_energy_plus
    name: Grid Consumption
  - entity: sensor.onemeter_energy_minus
    name: Grid Return
period: day
```

### Monthly Consumption Card

A card showing this month's and last month's usage:

```yaml
type: entities
entities:
  - entity: sensor.onemeter_this_month
    name: This Month's Consumption
    icon: mdi:calendar-month
  - entity: sensor.onemeter_previous_month
    name: Last Month's Consumption
    icon: mdi:calendar-month-outline
```

## Using with Utility Meter

You can combine the OneMeter integration with the built-in Utility Meter integration to track daily, weekly, or monthly consumption:

```yaml
# configuration.yaml
utility_meter:
  daily_energy:
    source: sensor.onemeter_energy_plus
    cycle: daily
  monthly_energy:
    source: sensor.onemeter_energy_plus
    cycle: monthly
```

Replace `sensor.onemeter_energy_plus` with your actual entity ID as needed.

## Automation Examples

### High Power Consumption Alert

```yaml
automation:
  - alias: "High Power Consumption Alert"
    trigger:
      platform: numeric_state
      entity_id: sensor.onemeter_power
      above: 5  # kW
      for:
        minutes: 10
    action:
      - service: notify.mobile_app
        data:
          title: "High Power Consumption"
          message: "Current power consumption is {{ states('sensor.onemeter_power') }} kW"
```

### Daily Energy Report

```yaml
automation:
  - alias: "Daily Energy Report"
    trigger:
      platform: time
      at: "23:00:00"
    action:
      - service: notify.mobile_app
        data:
          title: "Daily Energy Report"
          message: >
            Today's consumption: {{ states('sensor.daily_energy') }} kWh.
            This month so far: {{ states('sensor.onemeter_this_month') }} kWh.
```

## Using with Energy Cost Calculations

If you want to calculate energy costs, you can use template sensors:

```yaml
template:
  - sensor:
      - name: "Energy Cost Today"
        unit_of_measurement: "USD"
        state: "{{ (states('sensor.daily_energy') | float * 0.15) | round(2) }}"
        device_class: monetary
```

Replace `0.15` with your actual energy rate per kWh.

## Multiple OneMeter Devices

If you have multiple OneMeter devices configured in Home Assistant, make sure to adjust the entity IDs in your automations and dashboard configurations accordingly. Each device will have its own set of entities with unique IDs based on the device name.

## Lovelace Dashboard Example

Here's an example of a complete energy monitoring dashboard using OneMeter data:

```yaml
title: Energy Monitoring
views:
  - path: energy
    title: Energy
    badges: []
    cards:
      - type: vertical-stack
        cards:
          - type: sensor
            entity: sensor.onemeter_power
            name: Current Power
            graph: line
          - type: entity
            entity: sensor.onemeter_energy_plus
            name: Total Consumption
      - type: horizontal-stack
        cards:
          - type: entity
            entity: sensor.onemeter_this_month
            name: This Month
          - type: entity
            entity: sensor.onemeter_previous_month
            name: Last Month
      - type: entities
        entities:
          - entity: sensor.onemeter_tariff
            name: Current Tariff
          - entity: sensor.onemeter_battery_voltage
            name: Device Battery
```

Remember to replace the example entity IDs with your actual entity IDs.

For more advanced usage scenarios, refer to the [API documentation](api.md) to understand how to access the underlying data programmatically.