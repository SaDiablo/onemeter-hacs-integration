# Development Guide

This document provides information for developers who wish to contribute to the OneMeter Cloud integration for Home Assistant.

## Development Environment Setup

### Prerequisites

- Python 3.9 or higher
- Git
- A development instance of Home Assistant
- A OneMeter device or test account

### Setting Up the Development Environment

1. **Clone the Repository**

   ```bash
   git clone https://github.com/sadiablo/onemeter-hacs-integration.git
   cd onemeter-hacs-integration
   ```

2. **Create a Virtual Environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.dev.txt
   ```

4. **Install Pre-commit Hooks**

   ```bash
   pre-commit install
   ```

5. **Configure a Test Home Assistant Instance**

   For development, it's recommended to use a separate Home Assistant instance:

   ```bash
   mkdir test_homeassistant
   cd test_homeassistant
   hass -c . --skip-pip
   ```

6. **Link the Integration to Your Test Instance**

   Create a symbolic link from your development directory to the Home Assistant custom_components directory:

   ```bash
   # On Linux/Mac
   ln -s /path/to/onemeter-hacs-integration/custom_components/onemeter /path/to/test_homeassistant/custom_components/

   # On Windows (requires admin privileges)
   mklink /D C:\path\to\test_homeassistant\custom_components\onemeter C:\path\to\onemeter-hacs-integration\custom_components\onemeter
   ```

## Project Structure

```
onemeter-hacs-integration/
├── .github/                  # GitHub workflows and issue templates
├── custom_components/        # The actual integration code
│   └── onemeter/            
│       ├── __init__.py       # Integration initialization
│       ├── api.py            # OneMeter API client
│       ├── config_flow.py    # Configuration UI
│       ├── const.py          # Constants
│       ├── coordinator.py    # Data update coordinator
│       ├── manifest.json     # Integration manifest
│       ├── sensor.py         # Sensor platform
│       └── translations/     # UI translations
├── docs/                     # Documentation
├── tests/                    # Test suite
│   ├── conftest.py           # Test configuration
│   ├── test_api.py           # API tests
│   ├── test_config_flow.py   # Configuration flow tests
│   └── test_sensor.py        # Sensor tests
└── README.md                 # Project README
```

## Coding Standards

This project follows the Home Assistant coding standards:

- Use Python type hints
- Follow the [Home Assistant style guide](https://developers.home-assistant.io/docs/development_guidelines)
- Format code using Black
- Document public methods and classes with docstrings
- Keep line length to 100 characters

## Testing

### Running Tests

Run the test suite with pytest:

```bash
pytest
```

Run tests with coverage reporting:

```bash
pytest --cov=custom_components/onemeter
```

### Test Data

To test the integration without a real OneMeter device, mock responses can be found in the tests directory. These provide example API responses that simulate real OneMeter devices.

## Validation Tools

The project uses several validation tools:

- **Flake8**: Checks code style and quality
  ```bash
  flake8 custom_components/onemeter tests
  ```

- **Black**: Formats code
  ```bash
  black custom_components/onemeter tests
  ```

- **isort**: Sorts imports
  ```bash
  isort custom_components/onemeter tests
  ```

- **Pylint**: Static analysis
  ```bash
  pylint custom_components/onemeter tests
  ```

## GitHub Workflows

The repository uses several GitHub workflows for automation:

- **CI Testing**: Runs on every pull request to validate code quality and tests
- **HACS Validation**: Ensures compatibility with HACS
- **Hassfest**: Verifies the integration meets Home Assistant standards
- **Release Drafter**: Automatically creates release notes based on PR titles and labels

## Making a Contribution

1. Create a fork of the repository
2. Create a new branch for your feature
3. Make your changes, following the coding standards
4. Add or update tests as necessary
5. Verify all tests pass
6. Submit a pull request with a clear description of the changes

### Commit Message Guidelines

Use descriptive commit messages with a prefix indicating the type of change:

- `feat:` for features
- `fix:` for bug fixes
- `docs:` for documentation
- `test:` for tests
- `refactor:` for code refactoring
- `ci:` for CI/CD changes

Example: `feat: Add support for additional OBIS codes`

## Release Process

Releases follow semantic versioning:

1. Major version increases for breaking changes
2. Minor version increases for new features
3. Patch version increases for bug fixes

The release process is as follows:

1. Update the version number in `custom_components/onemeter/manifest.json`
2. Create a new release on GitHub
3. The release workflow will automatically build and package the integration

## Documentation

When adding new features, be sure to update the relevant documentation files in the `docs/` directory. Documentation is built automatically by the documentation workflow.

## Getting Help

If you have questions about development, feel free to:

1. Open an issue on GitHub with the "question" label
2. Join discussions in existing issues or pull requests
3. Refer to the [API documentation](api.md) for details on the OneMeter Cloud API