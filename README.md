# pipgeo: CLI for Unofficial Windows Geospatial Library Wheels

[![CI pipgeo](https://github.com/samapriya/pipgeo/actions/workflows/CI.yml/badge.svg)](https://github.com/samapriya/pipgeo/actions/workflows/CI.yml)
[![PyPI version](https://badge.fury.io/py/pipgeo.svg)](https://badge.fury.io/py/pipgeo)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

The amazing work of [Christoph Gohlke](https://www.cgohlke.com/) is the source of all this. The unofficial windows binaries page at lfd is no longer maintained, but Christoph has created a [dedicated GitHub repository with a subset of geospatial wheel assets](https://github.com/cgohlke/geospatial.whl). This tool is a straightforward CLI that can install binary wheels from the latest release assets with proper dependency ordering.

## Requirements

- **Python 3.11 or higher**
- **Windows OS only**

The precompiled wheels are only available for Windows on Python 3.11+.

## Installation

Installation is straightforward using pip. The tool automatically checks for new versions and informs you when updates are available.

```bash
pip install pipgeo
```

UV is automatically installed as a dependency for faster wheel installations.

## Features

- Automatic dependency resolution and installation order
- Fast installations using UV (with automatic fallback to pip)
- Download-only mode for offline installation
- Version checking and upgrade notifications
- Support for all major geospatial packages

## Supported Packages

Packages are installed in dependency order to ensure compatibility:

1. GDAL - Geospatial Data Abstraction Library
2. pyproj - Python interface to PROJ
3. shapely - Manipulation and analysis of geometric objects
4. cftime - Time-handling functionality
5. Fiona - Vector data format support (requires GDAL)
6. rasterio - Raster data access (requires GDAL)
7. netCDF4 - Network Common Data Form support
8. Rtree - Spatial indexing
9. pyogrio - Vectorized spatial vector file format I/O
10. Cartopy - Geospatial data processing (requires pyproj, shapely)
11. basemap - Plotting 2D data on maps (requires pyproj)

## Usage

### pipgeo release

Lists all available packages from the latest release for your system configuration, displayed in recommended installation order.

```bash
pipgeo release
```

This shows which packages are available for your Python version and architecture.

### pipgeo fetch

Fetches and installs a specific package from the latest release. Dependencies are automatically installed first if needed.

```bash
pipgeo fetch --lib gdal
```

Options:
- `--lib`: Package name to install (required)
- `--download-only`: Download wheel without installing
- `--output`: Output directory for downloaded wheels (default: wheels)
- `--quiet`: Suppress non-essential output
- `--use-pip`: Force use of pip instead of UV

Examples:
```bash
# Install GDAL with automatic dependency handling
pipgeo fetch --lib gdal

# Download rasterio wheel only
pipgeo fetch --lib rasterio --download-only --output ./my-wheels

# Install using pip instead of UV
pipgeo fetch --lib shapely --use-pip
```

### pipgeo sys

Installs all available geospatial packages from the release assets in the correct dependency order. This is the recommended way to set up a complete geospatial environment.

```bash
pipgeo sys
```

Options:
- `--download-only`: Download all wheels without installing
- `--output`: Output directory for downloaded wheels (default: wheels)
- `--quiet`: Suppress non-essential output
- `--use-pip`: Force use of pip instead of UV

Examples:
```bash
# Install all packages (recommended)
pipgeo sys

# Download all wheels for offline installation
pipgeo sys --download-only --output ./wheels

# Install using pip instead of UV
pipgeo sys --use-pip
```

## Performance

By default, pipgeo uses UV for installations, which is significantly faster than pip:
- 10-100x faster package installations
- Parallel downloads
- Better dependency resolution
- Efficient caching

If UV is not available or causes issues, pipgeo automatically falls back to pip. You can also force pip usage with the `--use-pip` flag.

## Upgrade Guide

### From v0.0.x to v0.1.0

**Breaking Changes:**
- Python 3.11+ now required (was 3.8+)
- UV is now the default installer (automatic fallback to pip)
- Flag changed: `--use-uv` removed, use `--use-pip` to force pip

**Benefits:**
- Much faster installations with UV
- Better dependency handling
- Modern Python features and type hints
- Cleaner package structure

To upgrade:
```bash
pip install --upgrade pipgeo
```

If you're on Python 3.8-3.10, you'll need to either:
- Upgrade to Python 3.11+, or
- Continue using pipgeo v0.0.7: `pip install "pipgeo<0.1.0"`

## Troubleshooting

### UV Installation Issues

If UV fails to install a package, pipgeo automatically falls back to pip. You can also force pip usage:

```bash
pipgeo sys --use-pip
```

### Package Not Found

Make sure you're running the latest version of pipgeo:

```bash
pip install --upgrade pipgeo
```

Then check available packages:

```bash
pipgeo release
```

### Python Version Issues

This tool requires Python 3.11 or higher. Check your version:

```bash
python --version
```

## Development

### Building from Source

```bash
git clone https://github.com/samapriya/pipgeo.git
cd pipgeo
pip install -e .
```

## Changelog

### v0.1.0
- BREAKING: Python 3.11+ now required
- UV is now the default installer with automatic fallback to pip
- Migrated to modern pyproject.toml configuration
- Added proper dependency ordering for all packages
- Improved error handling and user feedback
- Added `--use-pip` flag to force pip usage
- Removed unnecessary dependencies (natsort, setuptools from runtime)
- Updated to use SPDX license identifiers
- Enhanced CI/CD with UV support and linting
- Better type hints using Python 3.11+ features

### v0.0.7
- Added download-only mode and custom output directory support with `--download-only` and `--output` flags
- Improved error handling with retries for HTTP requests and better exception handling
- Refactored code structure with type hints, dataclasses, and proper module organization
- Added better dependency management and version checking with more robust comparison logic

### v0.0.6
- Release checker tool now checks if packages exist for installed Python version in latest release

### v0.0.5
- Release tool now prints available release packages and version number
- Improved PyPI version check functionality
- Fetch tool auto upgrades to latest version if new version is available in release

### v0.0.4
- Added dependency check from dependency tree
- Dependencies also installed using pipgeo

### v0.0.3
- Updated readme with instructions

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## Credits

All wheels are built and maintained by [Christoph Gohlke](https://www.cgohlke.com/) in the [geospatial.whl repository](https://github.com/cgohlke/geospatial.whl).

## Citation

If you use this tool in your research, please cite:

```bibtex
@software{pipgeo,
  author = {Roy, Samapriya},
  title = {pipgeo: CLI for Unofficial Windows Geospatial Library Wheels},
  year = {2024},
  url = {https://github.com/samapriya/pipgeo}
}
```
