"""Helper functions for OneMeter integration."""

def calculate_battery_percentage(voltage: float) -> int:
    """Calculate battery percentage from voltage.

    Battery percentage calculation based on:
    - 0% corresponds to 1.93V
    - 100% corresponds to 2.99V

    Args:
        voltage: Battery voltage in volts

    Returns:
        Integer percentage between 0-100
    """
    # Define voltage limits
    MIN_VOLTAGE = 1.93  # 0%
    MAX_VOLTAGE = 2.99  # 100%
    VOLTAGE_RANGE = MAX_VOLTAGE - MIN_VOLTAGE

    # Ensure voltage is within bounds
    bounded_voltage = max(MIN_VOLTAGE, min(voltage, MAX_VOLTAGE))

    # Calculate percentage
    percentage = ((bounded_voltage - MIN_VOLTAGE) / VOLTAGE_RANGE) * 100

    # Return as integer rounded to nearest percent
    return round(percentage)