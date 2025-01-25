def check_windows():
    """Check if running on Windows OS"""
    if not platform.system().lower() == "windows":
        sys.exit('This tool is only designed to fetch binaries for Windows OS')

def get_version_info(version1: str, version2: str) -> int:
    """
    Compare two version strings.
    Returns: 1 if version1 > version2, -1 if version1 < version2, 0 if equal
    """
    v1_parts = [int(v) for v in version1.split(".")]
    v2_parts = [int(v) for v in version2.split(".")]

    for i in range(max(len(v1_parts), len(v2_parts))):
        v1 = v1_parts[i] if i < len(v1_parts) else 0
        v2 = v2_parts[i] if i < len(v2_parts) else 0
        if v1 > v2:
            return 1
        elif v1 < v2:
            return -1
    return 0

def get_latest_version(package: str) -> str:
    """Get the latest version of a package from PyPI"""
    try:
        response = requests.get(f'https://pypi.org/pypi/{package}/json')
        response.raise_for_status()
        return response.json()['info']['version']
    except Exception as e:
        print(f"Error checking latest version: {str(e)}", file=sys.stderr)
        return "0.0.0"  # Return safe default if version check fails

def check_pipgeo_version() -> None:
    """Check if the current pipgeo version matches the latest PyPI version"""
    try:
        current_version = pkg_resources.get_distribution("pipgeo").version
        latest_version = get_latest_version('pipgeo')

        version_status = get_version_info(latest_version, current_version)

        border = "=" * 73
        if version_status == 1:
            print(f"\n{border}")
            print(f"Current version of pipgeo is {current_version}")
            print(f"Latest version available: {latest_version}")
            print(f"Upgrade available! Run: pip install --upgrade pipgeo")
            print(border)
        elif version_status == -1:
            print(f"\n{border}")
            print(f"Running development version {current_version}")
            print(f"Latest public release: {latest_version}")
            print(border)
    except pkg_resources.DistributionNotFound:
        print("Warning: Unable to determine pipgeo version", file=sys.stderr)
def release_list() -> None:
    """List all available packages for the current system"""
    sys_info = get_system_info()
    session = create_session()

    try:
        # Get latest release
        response = session.get(f'{GITHUB_BASE_URL}/releases/latest')
        if not response.history:
            raise Exception("Could not find latest release")

        tag = response.url.split('/')[-1]
        print(f"\nUsing latest release: {tag}")

        # Get release assets
        url = f"{GITHUB_BASE_URL}/releases/expanded_assets/{tag}"
        response = session.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        available_packages = []
        for a in soup.find_all('a', href=True):
            if sys_info in a['href']:
                filename = a['href'].split('/')[-1]
                package_name = filename.split('-')[0].lower()
                version = filename.split('-c')[0].split('-')[-1]
                available_packages.append((package_name, version))

        if available_packages:
            print(f"\nAvailable packages for your system ({sys_info}):")
            # Sort by package name
            for package_name, version in sorted(available_packages, key=lambda x: x[0]):
                print(f"- {package_name:<15} {version}")
        else:
            print("\nNo compatible packages found for your system")

    except Exception as e:
        print(f"Error listing releases: {str(e)}", file=sys.stderr)
        sys.exit(1)

import argparse
import json
import os
import platform
import re
import subprocess
import sys
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Set

import packaging.version as version_parser
import pkg_resources
import requests
from bs4 import BeautifulSoup
from natsort import natsorted
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

__copyright__ = """
    Copyright 2023 Samapriya Roy
    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at
       http://www.apache.org/licenses/LICENSE-2.0
    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""
__license__ = "Apache 2.0"

GITHUB_BASE_URL = "https://github.com/cgohlke/geospatial.whl"
CHUNK_SIZE = 5_000_000  # 5MB chunks for downloading

@dataclass
class PackageInfo:
    name: str
    version: str
    download_url: str

def get_system_info() -> str:
    """Get current system's Python and architecture info"""
    if not platform.system().lower() == "windows":
        sys.exit('This tool is only for Windows OS')

    version_tag = f"{sys.version_info[0]}{sys.version_info[1]}"
    arch = platform.uname()[4].lower()

    if arch not in {'amd64', 'arm64'}:
        return f'cp{version_tag}-cp{version_tag}-win{arch}'
    return f'cp{version_tag}-cp{version_tag}-win_{arch}'

def create_session() -> requests.Session:
    """Creates a requests session with retry logic"""
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

def get_package_info(package_name: str) -> PackageInfo:
    """Get package information including latest version and download URL"""
    session = create_session()
    sys_info = get_system_info()

    # Get latest release
    response = session.get(f'{GITHUB_BASE_URL}/releases/latest')
    if not response.history:
        raise Exception("Could not find latest release")

    tag = response.url.split('/')[-1]

    # Get release assets
    url = f"{GITHUB_BASE_URL}/releases/expanded_assets/{tag}"
    response = session.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    for a in soup.find_all('a', href=True):
        if sys_info in a['href']:
            filename = a['href'].split('/')[-1]
            pkg_name = filename.split('-')[0].lower()
            if pkg_name == package_name.lower():
                version = filename.split('-c')[0].split('-')[-1]
                download_url = f"https://github.com/{a['href']}"
                return PackageInfo(pkg_name, version, download_url)

    raise Exception(f"Package {package_name} not found")

def download_and_install_package(package: PackageInfo, download_only: bool = False, output_dir: Optional[Path] = None, quiet: bool = False) -> None:
    """Download and optionally install a package"""
    if download_only:
        if output_dir is None:
            output_dir = Path('wheels')
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / package.download_url.split('/')[-1]
    else:
        output_path = Path.home() / package.download_url.split('/')[-1]

    if download_only and output_path.exists():
        print(f"File already exists: {output_path.name}")
        return

    print(f'Downloading {output_path.name} to {output_path.parent}')
    response = requests.get(package.download_url, stream=True)
    response.raise_for_status()

    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            if chunk:
                f.write(chunk)

    print(f"Successfully downloaded: {output_path.name}")

    if not download_only:
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", str(output_path)],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"Successfully installed: {package.name} {package.version}")
        finally:
            output_path.unlink()

def sys_setup(download_only: bool = False, output_dir: Optional[Path] = None, quiet: bool = False) -> None:
    """System-wide installation or download of all packages"""
    packages = OrderedDict({
        'gdal': None,
        'pyproj': None,
        'shapely': None,
        'fiona': None,
        'netcdf4': None,
        'pygeos': None,
        'rtree': None,
        'rasterio': None,
        'basemap': None
    })

    if download_only:
        print(f"\nDownloading all packages{'to ' + str(output_dir) if output_dir else ''}")
        for package_name in packages:
            try:
                package = get_package_info(package_name)
                download_and_install_package(package, download_only=True, output_dir=output_dir, quiet=quiet)
            except Exception as e:
                print(f"Warning: Skipping {package_name} - {str(e)}")
        print("\nDownloads complete")

    else:
        installed = {pkg.key: pkg.version for pkg in pkg_resources.working_set}
        to_install = []
        to_upgrade = []

        for package_name in packages:
            try:
                package = get_package_info(package_name)
                if package_name not in installed:
                    to_install.append(package)
                elif version_parser.parse(package.version) > version_parser.parse(installed[package_name]):
                    to_upgrade.append((package, installed[package_name]))
            except Exception as e:
                print(f"Warning: Skipping {package_name} - {str(e)}")

        for package in to_install:
            print(f"\nInstalling {package.name}")
            download_and_install_package(package)

        for package, old_version in to_upgrade:
            print(f"\nUpgrading {package.name} from {old_version} to {package.version}")
            download_and_install_package(package)

        if not to_install and not to_upgrade:
            print('\nAll geospatial packages are installed and up to date')
        else:
            if to_install:
                print('\nNewly installed packages:')
                for pkg in to_install:
                    print(f"- {pkg.name} {pkg.version}")
            if to_upgrade:
                print('\nUpgraded packages:')
                for pkg, old_ver in to_upgrade:
                    print(f"- {pkg.name} {old_ver} -> {pkg.version}")

def fetch_geo(lib: str, download_only: bool = False, output_dir: Optional[Path] = None, quiet: bool = False) -> None:
    """Fetch and optionally install a specific package"""
    try:
        # Check dependencies first if installing
        if not download_only:
            dependencies = {
                'basemap': 'pyproj',
                'fiona': 'gdal',
                'rasterio': 'gdal'
            }
            if dep := dependencies.get(lib.lower()):
                installed_packages = {pkg.key for pkg in pkg_resources.working_set}
                if dep not in installed_packages:
                    print(f'Fetching dependency {dep}')
                    fetch_geo(dep)

        package = get_package_info(lib)

        if download_only:
                            download_and_install_package(package, download_only=True, output_dir=output_dir, quiet=quiet)
        else:
            installed_version = None
            try:
                installed_version = pkg_resources.get_distribution(lib).version
            except pkg_resources.DistributionNotFound:
                pass

            if installed_version:
                if version_parser.parse(package.version) > version_parser.parse(installed_version):
                    print(f"Upgrading {lib} from {installed_version} to {package.version}")
                    download_and_install_package(package)
                else:
                    print(f"Package {lib} {installed_version} is up to date")
            else:
                download_and_install_package(package)

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

def main():
    # Check Windows OS and pipgeo version first
    check_windows()
    check_pipgeo_version()

    parser = argparse.ArgumentParser(description="CLI for Unofficial Windows Geospatial library wheels")
    subparsers = parser.add_subparsers(dest='command')

    # System-wide installation
    sys_parser = subparsers.add_parser(
        "sys",
        help="Install all geospatial library assets"
    )
    sys_parser.add_argument(
        "--download-only",
        action="store_true",
        help="Only download the wheel files without installing"
    )
    sys_parser.add_argument(
        "--output",
        type=str,
        default="wheels",
        help="Output directory for downloaded wheel files (default: wheels)"
    )

    # List releases
    subparsers.add_parser(
        "release",
        help="Lists all GitHub release assets for your setup"
    )

    # Fetch specific package
    fetch_parser = subparsers.add_parser(
        "fetch",
        help="Download and install precompiled geospatial library"
    )
    fetch_parser.add_argument(
        "--lib",
        help="Geospatial library name (e.g., gdal, shapely)",
        required=True
    )
    fetch_parser.add_argument(
        "--download-only",
        action="store_true",
        help="Only download the wheel file without installing"
    )
    fetch_parser.add_argument(
        "--output",
        type=str,
        default="wheels",
        help="Output directory for downloaded wheel files (default: wheels)"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "sys":
        output_dir = Path(args.output) if args.download_only else None
        sys_setup(download_only=args.download_only, output_dir=output_dir)
    elif args.command == "release":
        release_list()
    elif args.command == "fetch":
        output_dir = Path(args.output) if args.download_only else None
        fetch_geo(args.lib, download_only=args.download_only, output_dir=output_dir, quiet=True)

if __name__ == "__main__":
    main()
