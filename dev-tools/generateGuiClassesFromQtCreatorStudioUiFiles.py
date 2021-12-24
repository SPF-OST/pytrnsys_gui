#!/usr/bin/python3.9

# Run from top-level directory

import pathlib as _pl
import shutil as _su
import subprocess as _sp


def main():
    print("Generating Python code from .ui files...")
    _generatePythonCodeFromUiFiles()
    print("...done.")

    print()

    print("Generating Python code for .qrc files...")
    _generatePythonCodeFromQrcFiles()
    print("...done.")


def _generatePythonCodeFromUiFiles():
    pyuicExecutableFilePath = _su.which("pyuic5")

    print(f"Using `pyuic5' executable at {pyuicExecutableFilePath}")

    currentDirPath = _pl.Path()

    uiFilePaths = currentDirPath.rglob("*.ui")
    for uiFilePath in uiFilePaths:
        generatedFilePath = _getGeneratedFilePath(uiFilePath, "UI")

        print(f"Generating {generatedFilePath} from {uiFilePath}...", end="")

        cmd = [pyuicExecutableFilePath, "-o", generatedFilePath, uiFilePath]
        _sp.run(cmd, check=True)

        print("done.")


def _generatePythonCodeFromQrcFiles():
    pyrccExecutableFilePath = _su.which("pyrcc5")

    print(f"Using `pyrcc5' executable at {pyrccExecutableFilePath}")

    currentDirPath = _pl.Path()

    qrcFilePaths = currentDirPath.rglob("*.qrc")
    for qrcFilePath in qrcFilePaths:
        generatedFilePath = _getGeneratedFilePath(qrcFilePath, "QRC")

        print(f"Generating {generatedFilePath} from {qrcFilePath}...", end="")

        cmd = [pyrccExecutableFilePath, "-o", generatedFilePath, qrcFilePath]
        _sp.run(cmd, check=True)

        print("done.")


def _getGeneratedFilePath(inputFilePath: _pl.Path, typePrefix: str) -> _pl.Path:
    underscoreOrEmpty = "_" if inputFilePath.name.startswith("_") else ""

    inputFilePathWithoutLeadingUnderscore = inputFilePath.parent / inputFilePath.name.lstrip("_")

    generatedFileName = (
        f"{underscoreOrEmpty}{typePrefix}_{inputFilePathWithoutLeadingUnderscore.with_suffix('').name}_generated.py"
    )
    generatedFilePath = inputFilePath.with_name(generatedFileName)
    return generatedFilePath


if __name__ == "__main__":
    main()
