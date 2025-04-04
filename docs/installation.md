# Installation

There are two ways to install the OneMeter Cloud integration in your Home Assistant instance: using HACS (recommended) or manual installation.

## HACS Installation (Recommended)

The Home Assistant Community Store (HACS) provides a convenient way to install and update custom components.

1. Make sure you have [HACS](https://hacs.xyz/) installed in your Home Assistant instance
   - If you don't have HACS installed yet, follow the [official installation guide](https://hacs.xyz/docs/installation/prerequisites)

2. Navigate to HACS in your Home Assistant sidebar

3. Go to "Integrations" section

4. Click the "+" button in the bottom right corner to add a new integration

5. Search for "OneMeter"

6. Select "OneMeter Cloud integration" from the results

7. Click "Install"

8. Restart Home Assistant to complete the installation
   - Go to Configuration → System → Restart or use the Restart button in Server Controls

## Manual Installation

If you prefer to install the integration manually:

1. Download the latest release from the [GitHub releases page](https://github.com/sadiablo/onemeter-hacs-integration/releases)

2. Extract the contents of the archive

3. Copy the `onemeter` directory to your Home Assistant `custom_components` directory
   - The location of this directory depends on your Home Assistant installation
   - For a standard installation, it's typically at `<config_directory>/custom_components/`
   - If the `custom_components` directory doesn't exist, you'll need to create it

4. Restart Home Assistant to complete the installation
   - Go to Configuration → System → Restart or use the Restart button in Server Controls

## Verifying the Installation

After restarting Home Assistant, you can verify that the integration was installed correctly:

1. Go to Configuration → Integrations
2. Click the "+ Add Integration" button
3. Search for "OneMeter"
4. If the installation was successful, you should see "OneMeter Cloud" in the search results

## What You'll Need

Before proceeding to the [Configuration](configuration.md) section, make sure you have:

1. Your OneMeter Cloud account credentials
2. An API key from your OneMeter Cloud account settings
   - The integration will use this key to automatically discover your OneMeter devices
   - You don't need to know your device IDs, as the integration will find them for you

Once you have your API key ready, proceed to the [Configuration](configuration.md) section to set up your OneMeter Cloud integration.