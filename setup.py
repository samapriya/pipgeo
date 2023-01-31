import setuptools
from setuptools import find_packages


def readme():
    with open("README.md") as f:
        return f.read()


setuptools.setup(
    name="pipgeo",
    version="0.0.5",
    packages=find_packages(),
    url="https://github.com/samapriya/pipgeo",
    install_requires=[
        "wheel>=0.38.4",
        "requests>=2.28.1",
        "beautifulsoup4>=4.11.1",
        "setuptools>=41.2.0"
    ],
    license="Apache 2.0",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Natural Language :: English",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: GIS",
    ],
    author="Samapriya Roy",
    author_email="samapriya.roy@gmail.com",
    description="CLI for Unofficial windows Geospatial library wheels",
    entry_points={
        "console_scripts": [
            "pipgeo=pipgeo.pipgeo:main",
        ],
    },
)
