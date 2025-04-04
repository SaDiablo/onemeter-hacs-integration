# Configuration

After installing the OneMeter Cloud integration, you'll need to configure it to connect to your OneMeter device through the OneMeter Cloud API.

## Prerequisites

Before configuring the integration, you'll need:

**API Key**: A valid OneMeter Cloud API key
- You can obtain this from your OneMeter Cloud account settings
- If you don't have an API key, log in to your OneMeter Cloud account and generate one

That's it! The integration will automatically discover all your OneMeter devices associated with your API key.

## Setting Up the Integration

1. Navigate to Home Assistant's **Configuration** panel
2. Select **Devices & Services**
3. Click the **+ Add Integration** button in the bottom right
4. Search for and select **OneMeter Cloud**
5. You'll be presented with a configuration form requesting your API credentials:
   - Enter your **API Key**
   - Click **Submit**

6. If the API key is valid, the integration will automatically:
   - Discover all your OneMeter devices
   - Present you with a list of available devices to add
   - Show devices that haven't been configured yet

7. Select the device you want to add from the dropdown list
8. Optionally provide a custom name for the device
9. Click **Submit**

## Configuration Options

After the initial setup, you can configure additional options for the integration:

1. From the **Devices & Services** page, find the OneMeter Cloud integration
2. Click on **Configure** to access the options menu
3. You can modify the following settings:
   - **Data Update Interval**: How frequently the integration should fetch new data from the OneMeter Cloud API (in seconds)
     - Default: 300 seconds (5 minutes)
     - Recommended: Keep this value above 60 seconds to avoid API rate limiting
     - Note: Setting this too low might exceed API rate limits

## Multiple Devices

If you have multiple OneMeter devices, you can add each one separately:

1. Complete the initial setup with your API key
2. The integration will show all available devices
3. Select one device to add
4. To add additional devices, go back to the integrations page and add the OneMeter integration again
5. The integration will automatically detect which devices are already configured and only show those that haven't been added yet

## Troubleshooting Configuration Issues

If you encounter problems during configuration:

- **Authentication Error**: Verify that your API key is correct
- **No Devices Found**: Ensure your OneMeter Cloud account has devices associated with it
- **Connection Errors**: Ensure your Home Assistant instance has internet connectivity and can reach the OneMeter Cloud services
- **Rate Limiting**: If you see API errors, try increasing the update interval in the configuration options

After configuration is complete, you'll have access to various [sensors](sensors.md) from your OneMeter device.