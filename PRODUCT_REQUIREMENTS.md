# Product Requirements Document: OneMeter Home Assistant Integration

**Version:** 1.0
**Date:** 2025-04-13
**Status:** Draft

## 1. Introduction

This document outlines the requirements for the OneMeter custom integration for Home Assistant. This integration allows users to connect their OneMeter cloud account to Home Assistant to monitor energy consumption and other data provided by OneMeter smart devices.

## 2. Goals

*   Provide Home Assistant users with seamless access to their OneMeter device data.
*   Enable monitoring of real-time and historical energy usage within Home Assistant.
*   Offer diagnostic information about the OneMeter device itself.
*   Ensure a reliable and robust integration following Home Assistant best practices.

## 3. Target Audience

*   Home Assistant users who own OneMeter smart energy monitoring devices.
*   Users interested in tracking detailed energy consumption, production (if applicable), and costs within their smart home environment.

## 4. Features

*   **Cloud API Communication:** Securely connect to the OneMeter Cloud API using a user-provided API key.
*   **Data Fetching:** Regularly poll the API for the latest readings and device status.
*   **Data Coordination:** Manage API polling efficiently using the Home Assistant DataUpdateCoordinator pattern.
*   **Sensor Entities:** Expose various data points from the OneMeter API as Home Assistant sensor entities, including:
    *   Energy Consumption (Positive Active Energy, Total & Tariffs)
    *   Energy Production (Negative Active Energy, Total & Tariffs)
    *   Reactive Energy (R1, R4, Total & Tariffs)
    *   Absolute Energy
    *   Instantaneous Power
    *   Monthly Usage Statistics (Current & Previous Month)
    *   Device Diagnostics (Battery Voltage, Battery Percentage, Meter Serial Number, Status, Errors, etc.)
    *   Tariff Information
*   **Configuration Flow:** Provide a UI-based configuration flow within Home Assistant for easy setup (API Key, Device ID).
*   **Device Registry Integration:** Create a device entry in the Home Assistant device registry representing the physical OneMeter device.
*   **Error Handling & Resiliency:** Implement robust error handling, API call retries, and connection validation.

## 5. Non-Goals

*   **Local Communication:** This integration will *not* communicate directly with OneMeter devices over the local network. It relies solely on the OneMeter Cloud API.
*   **Device Control:** The integration is read-only. It will *not* provide any functionality to control or configure the OneMeter device itself.
*   **User-Configurable Polling Interval:** The polling interval will be determined by the integration based on Home Assistant best practices for cloud polling (minimum 60 seconds) and will not be directly configurable by the end-user through the UI.
*   **Billing/Cost Calculation:** The integration will provide energy and tariff data, but will *not* perform cost calculations. This can be done using other Home Assistant features (e.g., Utility Meter, templates).

## 6. Design & Architecture

The integration follows standard Home Assistant architecture patterns:

1.  **`config_flow.py`**: Handles user interaction during setup via the UI to collect API Key and Device ID. Validates credentials against the API.
2.  **`api.py`**: Contains the `OneMeterApiClient` class responsible for all communication with the OneMeter Cloud REST API. Includes error handling, retries, and data parsing logic.
3.  **`coordinator.py`**: Implements the `OneMeterUpdateCoordinator` which schedules and manages periodic data fetching from the API using the `OneMeterApiClient`. It distributes the fetched data to entities.
4.  **`sensor.py`**: Defines the `OneMeterSensor` entities, mapping data from the coordinator to specific Home Assistant sensor states and attributes. Uses predefined sensor descriptions from `const.py`.
5.  **`const.py`**: Stores constants like API endpoints, OBIS codes, sensor mappings, domain name, etc.
6.  **`__init__.py`**: Handles the integration setup and unloading, initializes the API client and coordinator, and forwards the setup to the sensor platform.
7.  **`entity.py`**: Contains a base entity class if common logic is shared between entity types (currently used by `sensor.py`).
8.  **`helpers.py`**: Utility functions (e.g., calculating battery percentage).

## 7. Requirements

### 7.1. Functional Requirements

*   **FR1: Configuration:**
    *   The user must be able to add the integration via the Home Assistant UI.
    *   The config flow must prompt the user for their OneMeter API Key and Device ID.
    *   The config flow must validate the provided API Key and Device ID by attempting to fetch data from the `/devices/{device_id}` endpoint.
    *   On successful validation, a config entry must be created.
    *   On failure, an appropriate error message must be shown to the user.
*   **FR2: Data Fetching:**
    *   The integration must periodically poll the OneMeter Cloud API.
    *   The polling interval must adhere to Home Assistant cloud polling guidelines (minimum 60 seconds). The actual interval is determined by the coordinator's logic based on a configured refresh interval (e.g., 1, 5, 15 minutes), synchronized to the clock.
    *   API calls must be made asynchronously using `aiohttp`.
    *   The following API endpoints must be used:
        *   `devices/{device_id}`: To get the latest snapshot, including `lastReading` and `usage`.
        *   `devices/{device_id}/readings`: To potentially get more detailed or specific OBIS code readings if needed (currently used to ensure all mapped OBIS codes are fetched).
*   **FR3: Sensor Entities:**
    *   The integration must create sensor entities corresponding to the mappings defined in `SENSOR_TO_OBIS_MAP` and other relevant data points (e.g., monthly usage, battery percentage).
    *   Each sensor must have a unique ID derived from the config entry ID and the sensor key (e.g., `{entry_id}_energy_plus`).
    *   Sensors must correctly report their state based on the data received from the coordinator.
    *   Sensors must have appropriate units of measurement, device classes, state classes, and entity categories as defined in `SENSOR_TYPES`.
    *   If data for a sensor is unavailable from the API or coordinator, its state must be `None`.
    *   The `available` property of sensors must reflect the coordinator's update success status.
*   **FR4: Device Representation:**
    *   A single device entry must be created in the Home Assistant device registry for the configured OneMeter Device ID.
    *   Entities created by the integration must be linked to this device entry.
    *   The device entry should include identifiers (Device ID), manufacturer ("OneMeter"), and model information if available via the API.
*   **FR5: Error Handling:**
    *   API connection errors during setup must raise `ConfigEntryNotReady`.
    *   Invalid credentials during setup must result in a config flow error (`abort`).
    *   API errors during coordinator updates (e.g., timeouts, server errors, invalid responses) must be logged, and entities should become unavailable if the update fails repeatedly.
    *   The API client must implement a retry mechanism for transient errors (e.g., timeouts, 5xx server errors).
    *   Authentication (401) and Rate Limit (429) errors should be handled specifically and likely not retried automatically during a single update cycle.

### 7.2. Non-Functional Requirements

*   **NFR1: Reliability:** The integration must be resilient to temporary API outages and network issues through retries and proper error handling.
*   **NFR2: Performance:** API calls must be made asynchronously and not block the Home Assistant event loop. Concurrent API calls (`asyncio.gather`) should be used where appropriate (as currently implemented in the coordinator).
*   **NFR3: Usability:** The setup process must be straightforward via the Home Assistant UI. Sensor names and descriptions should be clear and understandable.
*   **NFR4: Security:** The API key must be stored securely by Home Assistant as part of the config entry and should not be logged. Communication with the API must use HTTPS.
*   **NFR5: Maintainability:** Code must follow Home Assistant development guidelines and the specific instructions provided for this repository (typing, formatting, linting, docstrings).

### 7.3. Technical Requirements

*   **TR1: Python Version:** Must be compatible with Python 3.13+.
*   **TR2: Home Assistant Version:** Must be compatible with recent Home Assistant Core versions (as defined in `manifest.json`).
*   **TR3: Dependencies:** Must use `aiohttp` for asynchronous HTTP requests. External dependencies should be minimized and declared in `manifest.json`.

## 8. Future Considerations

*   Support for configuring multiple OneMeter devices.
*   Discovery mechanism (if the API supports listing devices associated with an API key).
*   Adding support for more OBIS codes if requested by users and available via the API.
*   Investigating options for local polling if OneMeter devices offer a local API.
*   Adding diagnostic entities for API call success/failure rates or last update times.

## 9. Open Issues/Questions

*   What are the specific OneMeter Cloud API rate limits? (Documentation suggests ~1 request/minute).
*   Does the API provide device model information for the device registry?
*   Are there other useful OBIS codes commonly available that are not yet mapped?

