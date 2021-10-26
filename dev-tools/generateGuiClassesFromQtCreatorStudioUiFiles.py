#!/usr/bin/python3.9

# Run from top-level directory

import pathlib as _pl
import subprocess as _sp


def main():
    currentDirPath = _pl.Path()
    uiFilePaths = currentDirPath.rglob("*.ui")
    for uiFilePath in uiFilePaths:
        generatedFileName = f"_UI_{uiFilePath.with_suffix('').name}_generated.py"
        generatedFilePath = uiFilePath.with_name(generatedFileName)
        print(f"Generating {generatedFilePath} from {uiFilePath}...", end="")
        cmd = ["pyuic5", str(uiFilePath), "-o", str(generatedFilePath)]
        _sp.run(cmd, shell=True, check=True)
        print("done.")


if __name__ == "__main__":
    main()
