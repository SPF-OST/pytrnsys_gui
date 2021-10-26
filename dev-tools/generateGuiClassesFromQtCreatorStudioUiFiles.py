#!/usr/bin/python3.9

# Run from top-level directory

import pathlib as _pl
import subprocess as _sp
import shutil as _su


def main():
    pyuicExecutableFilePath = _su.which("pyuic5")

    print(f"Using `pyuic5' executable at {pyuicExecutableFilePath}")

    currentDirPath = _pl.Path()
    uiFilePaths = currentDirPath.rglob("*.ui")
    for uiFilePath in uiFilePaths:
        generatedFileName = f"_UI_{uiFilePath.with_suffix('').name}_generated.py"
        generatedFilePath = uiFilePath.with_name(generatedFileName)
        print(f"Generating {generatedFilePath} from {uiFilePath}...", end="")
        cmd = [pyuicExecutableFilePath, "-o", generatedFilePath, uiFilePath]
        _sp.run(cmd, check=True)
        print("done.")


if __name__ == "__main__":
    main()
