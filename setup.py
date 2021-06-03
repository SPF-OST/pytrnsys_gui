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
        p.relative_to(dataDirPath) for p in dataDirPath.rglob("*") if p.is_file()
    ]

    destDirSourcePathPairs = [
        _DestDirSourceFilePath(str("pytrnsys_gui_data" / p.parent), str("data" / p)) for p in dataFilePaths
    ]

    sortedPairs = sorted(destDirSourcePathPairs, key=lambda dp: dp.destDir)

    dataFilePairs = [
        (d, [dp.sourceFilePath for dp in dps])
        for d, dps in _it.groupby(sortedPairs, key=lambda dp: dp.destDir)
    ]

    return dataFilePairs


setuptools.setup(
    name="pytrnsys-gui",
    author="Martin Neugebauer",
    version_config=True,
    author_email="martin.neugebauer@ost.ch",
    description="A GUI for Trnsys",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SPF-OST/pytrnsys",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_data={
        "trnsysGUI": [
            "images/*.png",
            "images/*.svg",
            "templates/run.config",
            "templates/generic/*.ddck",
        ]
    },
    data_files=_getDataFilePairs(),
    entry_points={"console_scripts": ["pytrnsys-gui=trnsysGUI.GUI:main"]},
    install_requires=[
        "pytrnsys",
        "PyQT5",
        "matplotlib",
        "numpy",
        "pandas",
        "bokeh",
        "dataclasses_jsonschema",
        "appdirs",
    ],
    setup_requires=["setuptools-git-versioning"],
    python_requires=">=3.9",
)
