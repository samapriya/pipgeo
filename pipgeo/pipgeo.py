"""
Pipgeo - Unofficial Windows Geospatial Library Wheels Installer
Modern CLI for fetching and installing geospatial packages on Windows

SPDX-License-Identifier: Apache-2.0
"""

import argparse
import importlib.metadata
import platform
import shutil
import subprocess
import sys
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup
from packaging import version as pkg_version
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

GITHUB_BASE_URL = "https://github.com/cgohlke/geospatial.whl"
CHUNK_SIZE = 5_000_000  # 5MB chunks for downloading

# Install order based on dependencies
INSTALL_ORDER = [
    'gdal',      # Base dependency for fiona and rasterio
    'pyproj',    # Base dependency for cartopy and basemap
    'shapely',   # Base dependency for cartopy
    'cftime',    # Independent
    'fiona',     # Depends on GDAL
    'rasterio',  # Depends on GDAL
    'netcdf4',   # Independent
    'rtree',     # Independent
    'pyogrio',   # Independent
    'cartopy',   # Depends on pyproj, shapely
    'basemap'    # Depends on pyproj
]


@dataclass
class PackageInfo:
    name: str
    version: str
    download_url: str


def check_windows():
    """Check if running on Windows OS"""
    if not platform.system().lower() == "windows":
        sys.exit('This tool is only designed to fetch binaries for Windows OS')


def check_installer_available() -> tuple[str, bool]:
    """
    Check which installer is available, preferring UV.
    Returns: (installer_name, is_available)
    """
    if shutil.which('uv'):
        return ('uv', True)
    return ('pip', True)


def compare_version(version1: str, version2: str) -> int:
    """
    Compare two version strings using the packaging.version module.
    Returns: 1 if version1 > version2, -1 if version1 < version2, 0 if equal
    """
    v1 = pkg_version.parse(version1)
    v2 = pkg_version.parse(version2)
    if v1 > v2:
        return 1
    elif v1 < v2:
        return -1
    else:
        return 0


def get_latest_version(package: str) -> Optional[str]:
    """Get the latest version of a package from PyPI"""
    try:
        response = requests.get(f"https://pypi.org/pypi/{package}/json", timeout=5)
        response.raise_for_status()
        return response.json()["info"]["version"]
    except (requests.RequestException, KeyError) as e:
        print(f"Warning: Could not check latest version: {e}", file=sys.stderr)
        return None


def get_installed_version(package: str) -> Optional[str]:
    """Get the installed version of a package using importlib.metadata"""
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return None


def check_pipgeo_version() -> None:
    """Check if the current pipgeo version matches the latest PyPI version"""
    installed_version = get_installed_version("pipgeo")
    latest_version = get_latest_version("pipgeo")

    if not installed_version or not latest_version:
        return

    result = compare_version(latest_version, installed_version)

    border = "=" * 73
    if result == 1:
        print(f"\n{border}")
        print(f"Current version of pipgeo: {installed_version}")
        print(f"Latest version available: {latest_version}")
        print(f"Upgrade available! Run: pip install --upgrade pipgeo")
        print(border)
    elif result == -1:
        print(f"\n{border}")
        print(f"Running development version {installed_version}")
        print(f"Latest public release: {latest_version}")
        print(border)


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
                download_url = f"https://github.com{a['href']}"
                return PackageInfo(pkg_name, version, download_url)

    raise Exception(f"Package {package_name} not found for your system")


def download_package(package: PackageInfo, output_dir: Path, quiet: bool = False) -> Path:
    """Download a package and return the path to the downloaded file"""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / package.download_url.split('/')[-1]

    if output_path.exists():
        if not quiet:
            print(f"File already exists: {output_path.name}")
        return output_path

    if not quiet:
        print(f'Downloading {output_path.name}')

    response = requests.get(package.download_url, stream=True)
    response.raise_for_status()

    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            if chunk:
                f.write(chunk)

    if not quiet:
        print(f"Successfully downloaded: {output_path.name}")

    return output_path


def install_wheel_with_uv(wheel_path: Path, package_name: str, quiet: bool = False) -> bool:
    """Install a wheel file using uv"""
    try:
        cmd = [
            'uv', 'pip', 'install',
            f'{package_name} @ file:///{wheel_path.absolute().as_posix()}'
        ]
        
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        
        if not quiet:
            print(f"Installed with uv: {package_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing with uv: {e.stderr}", file=sys.stderr)
        return False


def install_wheel_with_pip(wheel_path: Path, package_name: str, quiet: bool = False) -> bool:
    """Install a wheel file using pip"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", str(wheel_path)],
            check=True,
            capture_output=True,
            text=True
        )
        
        if not quiet:
            print(f"Installed with pip: {package_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing with pip: {e.stderr}", file=sys.stderr)
        return False


def download_and_install_package(
    package: PackageInfo,
    download_only: bool = False,
    output_dir: Optional[Path] = None,
    quiet: bool = False,
    force_pip: bool = False
) -> None:
    """Download and optionally install a package"""
    if download_only:
        if output_dir is None:
            output_dir = Path('wheels')
        download_package(package, output_dir, quiet)
    else:
        # Download to temp directory
        temp_dir = Path.home() / '.pipgeo_temp'
        wheel_path = download_package(package, temp_dir, quiet)
        
        try:
            # Auto-detect best installer unless forced to use pip
            if force_pip:
                install_wheel_with_pip(wheel_path, package.name, quiet)
            else:
                installer, available = check_installer_available()
                if installer == 'uv':
                    success = install_wheel_with_uv(wheel_path, package.name, quiet)
                    if not success:
                        if not quiet:
                            print(f"Falling back to pip for {package.name}")
                        install_wheel_with_pip(wheel_path, package.name, quiet)
                else:
                    install_wheel_with_pip(wheel_path, package.name, quiet)
        finally:
            # Clean up temp file
            try:
                wheel_path.unlink()
            except:
                pass


def sys_setup(
    download_only: bool = False,
    output_dir: Optional[Path] = None,
    quiet: bool = False,
    force_pip: bool = False
) -> None:
    """System-wide installation or download of all packages"""
    # Use install order
    packages = OrderedDict({pkg: None for pkg in INSTALL_ORDER})

    # Show which installer will be used
    if not download_only and not quiet:
        installer, _ = check_installer_available()
        if force_pip:
            print("Using pip (forced)")
        else:
            if installer == 'uv':
                print("Using uv for faster installation")
            else:
                print("Using pip (uv not found - install with: pip install uv)")

    if download_only:
        print(f"\nDownloading all packages{' to ' + str(output_dir) if output_dir else ''}")
        for package_name in packages:
            try:
                package = get_package_info(package_name)
                download_and_install_package(
                    package,
                    download_only=True,
                    output_dir=output_dir,
                    quiet=quiet
                )
            except Exception as e:
                print(f"Warning: Skipping {package_name} - {str(e)}")
        print("\nDownloads complete")
    else:
        installed = {
            pkg: get_installed_version(pkg)
            for pkg in packages.keys()
        }
        to_install = []
        to_upgrade = []

        for package_name in packages:
            try:
                package = get_package_info(package_name)
                installed_ver = installed.get(package_name)

                if installed_ver is None:
                    to_install.append(package)
                elif compare_version(package.version, installed_ver) > 0:
                    to_upgrade.append((package, installed_ver))
            except Exception as e:
                print(f"Warning: Skipping {package_name} - {str(e)}")

        # Install in dependency order
        for package in to_install:
            print(f"\nInstalling {package.name}")
            download_and_install_package(package, force_pip=force_pip)

        for package, old_version in to_upgrade:
            print(f"\nUpgrading {package.name} from {old_version} to {package.version}")
            download_and_install_package(package, force_pip=force_pip)

        if not to_install and not to_upgrade:
            print('\nAll geospatial packages are installed and up to date')
        else:
            if to_install:
                print('\nNewly installed packages:')
                for pkg in to_install:
                    print(f"  - {pkg.name} {pkg.version}")
            if to_upgrade:
                print('\nUpgraded packages:')
                for pkg, old_ver in to_upgrade:
                    print(f"  - {pkg.name} {old_ver} -> {pkg.version}")


def fetch_geo(
    lib: str,
    download_only: bool = False,
    output_dir: Optional[Path] = None,
    quiet: bool = False,
    force_pip: bool = False
) -> None:
    """Fetch and optionally install a specific package"""
    try:
        # Check dependencies first if installing
        if not download_only:
            dependencies = {
                'basemap': ['pyproj'],
                'fiona': ['gdal'],
                'rasterio': ['gdal'],
                'cartopy': ['pyproj', 'shapely']
            }
            
            if deps := dependencies.get(lib.lower()):
                for dep in deps:
                    if not get_installed_version(dep):
                        print(f'Installing dependency: {dep}')
                        fetch_geo(dep, force_pip=force_pip)

        package = get_package_info(lib)

        if download_only:
            download_and_install_package(
                package,
                download_only=True,
                output_dir=output_dir,
                quiet=quiet
            )
        else:
            if not quiet:
                installer, _ = check_installer_available()
                if force_pip:
                    print("Using pip (forced)")
                elif installer == 'uv':
                    print("Using uv for faster installation ⚡")
                else:
                    print("Using pip (install uv for faster installations: pip install uv)")
            
            installed_version = get_installed_version(lib)

            if installed_version:
                if compare_version(package.version, installed_version) > 0:
                    print(f"Upgrading {lib} from {installed_version} to {package.version}")
                    download_and_install_package(package, force_pip=force_pip)
                else:
                    print(f"Package {lib} {installed_version} is up to date")
            else:
                download_and_install_package(package, force_pip=force_pip)

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


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
            print("\n(Packages listed in recommended install order):")
            # Sort by install order, then alphabetically
            sorted_packages = []
            for pkg_name in INSTALL_ORDER:
                matching = [p for p in available_packages if p[0] == pkg_name]
                if matching:
                    sorted_packages.extend(matching)
            
            # Add any remaining packages not in install order
            remaining = [p for p in available_packages if p[0] not in INSTALL_ORDER]
            sorted_packages.extend(sorted(remaining, key=lambda x: x[0]))
            
            for i, (package_name, version) in enumerate(sorted_packages):
                if package_name in INSTALL_ORDER:
                    order_num = f"[{INSTALL_ORDER.index(package_name) + 1:2d}]"
                    print(f"  {order_num} {package_name:<15} {version}")
                else:
                    print(f"      {package_name:<15} {version}")
        else:
            print("\nNo compatible packages found for your system")

    except Exception as e:
        print(f"Error listing releases: {str(e)}", file=sys.stderr)
        sys.exit(1)


def main():
    # Check Windows OS and pipgeo version first
    check_windows()
    check_pipgeo_version()

    parser = argparse.ArgumentParser(
        description="CLI for Unofficial Windows Geospatial library wheels",
        epilog="By default, uses uv for faster installation (falls back to pip if unavailable)"
    )
    subparsers = parser.add_subparsers(dest='command')

    # System-wide installation
    sys_parser = subparsers.add_parser(
        "sys",
        help="Install all geospatial library assets (in dependency order)"
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
    sys_parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress non-essential output"
    )
    sys_parser.add_argument(
        "--use-pip",
        action="store_true",
        help="Force use of pip instead of uv"
    )

    # List releases
    subparsers.add_parser(
        "release",
        help="List all available packages with install order"
    )

    # Fetch specific package
    fetch_parser = subparsers.add_parser(
        "fetch",
        help="Download and install a specific geospatial library"
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
    fetch_parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress non-essential output"
    )
    fetch_parser.add_argument(
        "--use-pip",
        action="store_true",
        help="Force use of pip instead of uv"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "sys":
        output_dir = Path(args.output) if args.download_only else None
        quiet = getattr(args, 'quiet', False)
        force_pip = getattr(args, 'use_pip', False)
        sys_setup(
            download_only=args.download_only,
            output_dir=output_dir,
            quiet=quiet,
            force_pip=force_pip
        )
    elif args.command == "release":
        release_list()
    elif args.command == "fetch":
        output_dir = Path(args.output) if args.download_only else None
        quiet = getattr(args, 'quiet', False)
        force_pip = getattr(args, 'use_pip', False)
        fetch_geo(
            args.lib,
            download_only=args.download_only,
            output_dir=output_dir,
            quiet=quiet,
            force_pip=force_pip
        )


if __name__ == "__main__":
    main()
