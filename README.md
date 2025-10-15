# Graphical user interface for pytrnsys

[![Coverage Status](https://coveralls.io/repos/github/SPF-OST/pytrnsys_gui/badge.svg?branch=master)](https://coveralls.io/github/SPF-OST/pytrnsys_gui?branch=master) [![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=SPF-OST_pytrnsys_gui&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=SPF-OST_pytrnsys_gui) [![DOI](https://zenodo.org/badge/269046674.svg)](https://doi.org/10.5281/zenodo.17276890)


## Overview

A short presentation (15 min) of pytrnsys and its features can be found in the following 
[YouTube video](https://www.youtube.com/watch?v=B1BSjYRKuVM).

## Documentation

You can find the documentation under https://pytrnsys.readthedocs.io/ 

## Installation

You'll need `TRNSYS` (at least version 17, preferably version 18, 32 bit)  installed on your machine.

### Binary installation / User installation

#### Installation

##### Latest stable release

This version is recommended for **non-SPF users** and/or everyone interested in the most recent stable release
possibly missing the latest features.

Go to [Releases](https://github.com/SPF-OST/pytrnsys_gui/releases) and download the `.zip` file included in
the latest Release Build:

![Latest Versioned Release](doc/release.png)

(Note that the version will vary as newer versions are being published)

##### Bleeding-edge version

This version is recommended for **SPF users** and/or everyone wanting to get the latest and greatest but not minding the fact
that this version is less stable (i.e. can contain more bugs/errors) than the latest stable release.

Go to [Releases](https://github.com/SPF-OST/pytrnsys_gui/releases) and download the `.zip` file included in
the `bleeding-edge` Development Build:

![Bleeding Edge Release](doc/bleeding-edge.png)

#### Post-installation

Copy `pytrnsys` custom TRNSYS types in the form of compiled DLLs from

    pytrnsys_data\data\ddcks\dlls
    
to the respective folder of your TRNSYS installation:

    ...\UserLib\ReleaseDLLs

#### Troubleshooting
`pytrnsys-gui.bat` writes logging messages into the `pytrnsys-gui.log` file located in the same directory
as the `.bat` file. The `.log` file might give you some hints as to what happened if something doesn't
work or if `pytrnsys-gui.bat` has crashed.

## Developers
See [DEVELOPER-README.md](DEVELOPER-README.md).