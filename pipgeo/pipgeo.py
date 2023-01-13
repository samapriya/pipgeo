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

import argparse
import json
import os
import platform
import subprocess
import sys
from collections import OrderedDict
from os.path import expanduser

import pkg_resources
import requests
from bs4 import BeautifulSoup

if not str(platform.system().lower()) == "windows":
    sys.exit('This tool is only designed to fetch binaries for windows OS')
installed_packages = [pkg.key for pkg in pkg_resources.working_set]


class Solution:
    def compareVersion(self, version1, version2):
        versions1 = [int(v) for v in version1.split(".")]
        versions2 = [int(v) for v in version2.split(".")]
        for i in range(max(len(versions1), len(versions2))):
            v1 = versions1[i] if i < len(versions1) else 0
            v2 = versions2[i] if i < len(versions2) else 0
            if v1 > v2:
                return 1
            elif v1 < v2:
                return -1
        return 0


ob1 = Solution()

# Get package version


def pipgeo_version():
    url = "https://pypi.org/project/pipgeo/"
    source = requests.get(url)
    html_content = source.text
    soup = BeautifulSoup(html_content, "html.parser")
    company = soup.find("h1")
    vcheck = ob1.compareVersion(
        company.string.strip().split(" ")[-1],
        pkg_resources.get_distribution("pipgeo").version,
    )
    if vcheck == 1:
        print(
            "\n"
            + "========================================================================="
        )
        print(
            "Current version of pipgeo is {} upgrade to lastest version: {}".format(
                pkg_resources.get_distribution("pipgeo").version,
                company.string.strip().split(" ")[-1],
            )
        )
        print(
            "========================================================================="
        )
    elif vcheck == -1:
        print(
            "\n"
            + "========================================================================="
        )
        print(
            "Possibly running staging code {} compared to pypi release {}".format(
                pkg_resources.get_distribution("pipgeo").version,
                company.string.strip().split(" ")[-1],
            )
        )
        print(
            "========================================================================="
        )


pipgeo_version()


def sys_parse():
    version_tag = f"{sys.version_info[0]}{sys.version_info[1]}"
    exc_name = platform.uname()[4].lower()
    ex_list = ['amd64', 'arm64']
    if not exc_name in ex_list:
        overall_sys = f'cp{version_tag}-cp{version_tag}-win{exc_name}'
    else:
        overall_sys = f'cp{version_tag}-cp{version_tag}-win_{exc_name}'
    return overall_sys


def download_file(url, lib):
    home_dir = expanduser("~")
    filename = url.split('/')[-1]
    full_filename = os.path.join(home_dir, filename)

    if not lib in installed_packages:
        if not os.path.exists(full_filename):
            print(f'Downloading whl file to {full_filename}')
            resp = requests.get(url, stream=True)
            with open(full_filename, 'wb') as file_desc:
                for chunk in resp.iter_content(chunk_size=5000000):
                    file_desc.write(chunk)
            subprocess.call(
                f"{sys.executable} -m pip install {full_filename}", shell=True
            )
            os.unlink(full_filename)
        else:
            print(f'File already exists: SKIPPING {filename}')
    else:
        print(f"Requirement already satisified {lib} installed")


def fetch_geo(lib):
    lib_list = []
    match_list = []
    response = requests.get(
        'https://github.com/cgohlke/geospatial.whl/releases/latest')
    if response.history:
        tag = (response.url.split('/')[-1])

    url = f"https://github.com/cgohlke/geospatial.whl/releases/expanded_assets/{tag}"
    source = requests.get(url)
    html_content = source.text
    soup = BeautifulSoup(html_content, "html.parser")

    for a in soup.find_all('a', href=True):
        if sys_parse() in a['href']:
            if lib.lower() in a['href'].split('/')[-1].split('-')[0].lower():
                download_url = f"https://github.com/{a['href']}"
                match_list.append(download_url)
                download_file(download_url, lib)
            else:
                lib_list.append(a['href'].split('/')[-1].split('-')[0].lower())
    if not match_list:
        print('Current available packages: {}'.format(lib_list))


def fetch_from_parser(args):
    fetch_geo(
        lib=args.lib
    )


def release_list():
    lib_list = []
    response = requests.get(
        'https://github.com/cgohlke/geospatial.whl/releases/latest')
    if response.history:
        tag = (response.url.split('/')[-1])

    url = f"https://github.com/cgohlke/geospatial.whl/releases/expanded_assets/{tag}"
    source = requests.get(url)
    html_content = source.text
    soup = BeautifulSoup(html_content, "html.parser")

    for a in soup.find_all('a', href=True):
        if sys_parse() in a['href']:
            lib_list.append(a['href'].split('/')[-1].split('-')[0].lower())
    print(json.dumps(lib_list, indent=2))


def release_from_parser(args):
    release_list()


def sys_setup():
    installer_list = []
    lib_list = {4: 'fiona', 1: 'gdal', 5: 'netcdf4', 6: 'pygeos',
                2: 'pyproj', 8: 'rasterio', 7: 'rtree', 3: 'shapely', 9: 'basemap'}
    for key, lib in OrderedDict(sorted(lib_list.items())).items():
        if not lib in installed_packages:
            installer_list.append(lib)
            fetch_geo(lib)
    if len(installer_list) == 0:
        print('\n'+'All GEO packages installed')


def sys_from_parser(args):
    sys_setup()


def main(args=None):
    parser = argparse.ArgumentParser(
        description="CLI for Unofficial windows Geospatial library wheels")
    subparsers = parser.add_subparsers()

    parser_sys = subparsers.add_parser(
        "sys", help="Install all geospatial library assets from GitHub release assets"
    )
    parser_sys.set_defaults(func=sys_from_parser)

    parser_release = subparsers.add_parser(
        "release", help="Lists all GitHub release assets for your setup"
    )
    parser_release.set_defaults(func=release_from_parser)

    parser_fetch = subparsers.add_parser(
        "fetch", help="Download and install precompiled geospatial library"
    )
    required_named = parser_fetch.add_argument_group(
        "Required named arguments.")
    required_named.add_argument(
        "--lib", help="Geospatial library from the release list like gdal or shapely", required=True)
    parser_fetch.set_defaults(func=fetch_from_parser)

    args = parser.parse_args()

    try:
        func = args.func
    except AttributeError:
        parser.error("too few arguments")
    func(args)


if __name__ == "__main__":
    main()
