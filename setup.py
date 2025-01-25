import setuptools
from setuptools import find_packages

# Read README.md once
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setuptools.setup(
    name="pipgeo",
    version="0.0.7",  # Incremented version
    packages=find_packages(),
    url="https://github.com/samapriya/pipgeo",
    install_requires=[
        "wheel>=0.42.0",
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.3",
        "setuptools>=69.0.3",
        "natsort>=8.4.0"
    ],
    license="Apache 2.0",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Natural Language :: English",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: GIS",
    ],
    author="Samapriya Roy",
    author_email="samapriya.roy@gmail.com",
    description="CLI for Unofficial windows Geospatial library wheels",
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "pipgeo=pipgeo.pipgeo:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/samapriya/pipgeo/issues",
        "Source": "https://github.com/samapriya/pipgeo",
    },
)
