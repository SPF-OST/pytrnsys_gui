#!/usr/bin/python3.9

# Run from top-level directory

import pathlib as _pl
import subprocess as _sp
import sysconfig as _sysconfig

_SCRIPTS_DIR = _pl.Path(_sysconfig.get_path("scripts"))
_PYUIC5_FILE_PATH = _SCRIPTS_DIR / "pyuic5"
_PYRCC5_FILE_PATH = _SCRIPTS_DIR / "pyrcc5"


def main():
    print("Generating Python code from .ui files...")
    _generatePythonCodeFromUiFiles()
    print("...done.")

    print()

    print("Generating Python code for .qrc files...")
    _generatePythonCodeFromQrcFiles()
    print("...done.")


def _generatePythonCodeFromUiFiles():
    print(f"Using pyuic5 executable from {_PYUIC5_FILE_PATH}.")

    trnsysGuiDirPath = _pl.Path("trnsysGUI")

    uiFilePaths = trnsysGuiDirPath.rglob("*.ui")
    for uiFilePath in uiFilePaths:
        generatedFilePath = _getGeneratedFilePath(uiFilePath, "UI")

        print(f"Generating {generatedFilePath} from {uiFilePath}...", end="")

        cmd = [_PYUIC5_FILE_PATH, "-o", generatedFilePath, uiFilePath]
        _sp.run(cmd, check=True)

        print("done.")


def _generatePythonCodeFromQrcFiles():
    print(f"Using pyrcc5 executable from {_PYRCC5_FILE_PATH}.")

    currentDirPath = _pl.Path()

    qrcFilePaths = currentDirPath.rglob("*.qrc")
    for qrcFilePath in qrcFilePaths:
        generatedFilePath = _getGeneratedFilePath(qrcFilePath, "QRC")

        print(f"Generating {generatedFilePath} from {qrcFilePath}...", end="")

        cmd = [_PYRCC5_FILE_PATH, "-o", generatedFilePath, qrcFilePath]
        _sp.run(cmd, check=True)

        print("done.")


def _getGeneratedFilePath(
    inputFilePath: _pl.Path, typePrefix: str
) -> _pl.Path:
    underscoreOrEmpty = "_" if inputFilePath.name.startswith("_") else ""

    inputFilePathWithoutLeadingUnderscore = (
        inputFilePath.parent / inputFilePath.name.lstrip("_")
    )

    generatedFileName = (
        f"{underscoreOrEmpty}{typePrefix}"
        f"_{inputFilePathWithoutLeadingUnderscore.with_suffix('').name}_generated.py"
    )
    generatedFilePath = inputFilePath.with_name(generatedFileName)
    return generatedFilePath


if __name__ == "__main__":
    main()
