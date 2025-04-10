# pylint: skip-file
# type: ignore

import setuptools
import pathlib as _pl
import itertools as _it
import dataclasses as _dc

with open("README.md", "r") as fh:
    long_description = fh.read()


@_dc.dataclass
class _DestDirSourceFilePath:
    destDir: str
    sourceFilePath: str


def _getDataFilePairs():
    dataDirPath = _pl.Path(__file__).parent / "data"

    dataFilePaths = [
        p.relative_to(dataDirPath)
        for p in dataDirPath.rglob("*")
        if p.is_file()
    ]

    destDirSourcePathPairs = [
        _DestDirSourceFilePath(
            str("pytrnsys_gui_data" / p.parent), str("data" / p)
        )
        for p in dataFilePaths
    ]

    sortedPairs = sorted(destDirSourcePathPairs, key=lambda dp: dp.destDir)

    dataFilePairs = [
        (d, [dp.sourceFilePath for dp in dps])
        for d, dps in _it.groupby(sortedPairs, key=lambda dp: dp.destDir)
    ]

    return dataFilePairs


def _getInstallRequirements():
    requirementsFile = (
        _pl.Path(__file__).parent / "requirements" / "release-3rd-party.in"
    )
    lines = requirementsFile.read_text().split("\n")
    requirements = [l for l in lines if l.strip() and not l.startswith("#")]
    return requirements


_MASTER_VERSION_TEMPLATE = "0.0.0+master.{sha}"

setuptools.setup(
    name="pytrnsys-gui",
    author="Institute for Solar Technology (SPF), OST Rapperswil",
    setuptools_git_versioning={
        "enabled": True,
        "template": _MASTER_VERSION_TEMPLATE,
        "dev_template": _MASTER_VERSION_TEMPLATE,
        "dirty_template": f"{_MASTER_VERSION_TEMPLATE}.dirty",
    },
    author_email="damian.birchler@ost.ch",
    description="A GUI for Trnsys",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SPF-OST/pytrnsys",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GPL3 License",
        "Operating System :: OS Independent",
    ],
    package_data={
        "trnsysGUI": [
            "images/*.png",
            "images/*.svg",
            "templates/run.config",
            "templates/generic/*.ddck",
        ],
        "trnsysGUI.components.plugin": ["data/*/*.svg", "data/*/*.yaml"],
        "trnsysGUI.proforma": ["templates/ddck.jinja", "xmltmf.xsd"],
    },
    data_files=_getDataFilePairs(),
    install_requires=_getInstallRequirements(),
    python_requires=">=3.12",
)
