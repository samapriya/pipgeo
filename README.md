# pipgeo: CLI for Unofficial windows Geospatial library wheels

[![CI pipgeo](https://github.com/samapriya/pipgeo/actions/workflows/CI.yml/badge.svg)](https://github.com/samapriya/pipgeo/actions/workflows/CI.yml)

The amazing work of [Christoph Gohlke](https://www.cgohlke.com/) is the source of all this, though the unofficial windows binaries page at lfd is no longer maintained. Christoph has created a [dedicated GitHub repository with a subset of geospatial wheel assets that have been released](https://github.com/cgohlke/geospatial.whl). This tool is a straightforward CLI that can pre-install a binary wheel from the latest release assets.

#### Installation

Installation is pretty simple use. The tool automatically also checks as new versions are released and informs you.

**The precompiled wheels and as such the tool is only available for python 3.8 and higher**

```
pip install pipgeo
```

![pipgeo-install](https://user-images.githubusercontent.com/6677629/212253241-0bed60f5-c83b-4fbb-b79d-b63d543eb928.gif)

#### pipgeo release
This tool fetches release assets from the latest release and lists them to the user incase they are looking for a specific packages and or want to install a specific package.

Example usage

```
pipgeo release
```

![pipgeo-list](https://user-images.githubusercontent.com/6677629/212253240-1d928f64-9004-4254-b80c-0b3b08a01437.gif)

#### pipgeo fetch
This tool will allow you to fetch a specific package from the latest release and install it. You can search based on the package list returned form the release tool.

Example usage

```
pipgeo fetch --lib gdal
```

![pipgeo-fetch](https://user-images.githubusercontent.com/6677629/212253239-9a9381e7-fe2d-4008-a4a4-8418fa687597.gif)

#### pipgeo sys
This will install all packages from the release assets onto your system. It maintains prerequisite and dependency order to allow for easy installation.

Example usage

```
pipgeo sys
```

![pipgeo-sys](https://user-images.githubusercontent.com/6677629/212253237-9bbd32c0-3312-4a8b-8661-887f7422b45b.gif)

### Changelog

#### v0.0.5
- release tool now print available release packages and version number
- improved pypi version check functionality
- fetch tool auto upgrades to latest version if new version is available in release

#### v0.0.4
- added dependency check from dependency tree
- dependencies also installed using pipgeo

#### v0.0.3
- updated readme with instructions
