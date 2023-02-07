#!/usr/bin/python3.9

# Run from top-level directory

import pathlib as _pl
import subprocess as _sp

import sys

_VENV_BIN_DIR_PATH = _pl.Path(sys.executable).parent


def main():
    print("Generating Python code from .ui files...")
    _generatePythonCodeFromUiFiles()
    print("...done.")

    print()

    print("Generating Python code for .qrc files...")
    _generatePythonCodeFromQrcFiles()
    print("...done.")


def _generatePythonCodeFromUiFiles():
    currentDirPath = _pl.Path()

    uiFilePaths = currentDirPath.rglob("*.ui")
    for uiFilePath in uiFilePaths:
        generatedFilePath = _getGeneratedFilePath(uiFilePath, "UI")

        print(f"Generating {generatedFilePath} from {uiFilePath}...", end="")

        cmd = [_VENV_BIN_DIR_PATH / "pyuic5", "-o", generatedFilePath, uiFilePath]
        _sp.run(cmd, check=True)

        print("done.")


def _generatePythonCodeFromQrcFiles():
    currentDirPath = _pl.Path()

    qrcFilePaths = currentDirPath.rglob("*.qrc")
    for qrcFilePath in qrcFilePaths:
        generatedFilePath = _getGeneratedFilePath(qrcFilePath, "QRC")

        print(f"Generating {generatedFilePath} from {qrcFilePath}...", end="")

        cmd = [_VENV_BIN_DIR_PATH / "pyrcc5", "-o", generatedFilePath, qrcFilePath]
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
