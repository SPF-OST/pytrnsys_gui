import sys

import http.client as _htc
import pathlib as _pl
import shutil as _sh
import sys as _sys
import subprocess as _sp
import typing as _tp
import urllib.request as _urlreq
import urllib.parse as _urlp
import zipfile as _zip

PYTHON_312_DIST_DIR_PATH = _pl.Path(r"C:\Program Files\Python312")

RELATIVE_TK_TCL_FILE_OR_DIR_PATHS_TO_COPY = map(
    _pl.Path,
    [
        r"tcl",
        r"Lib\tkinter",
        r"DLLs\tcl86t.dll",
        r"DLLs\tk86t.dll",
        r"DLLs\_tkinter.pyd",
        r"DLLs\zlib1.dll",
    ],
)

RELEASE_DIR_PATH = _pl.Path(__file__).parent
URL_FILE_PATH = RELEASE_DIR_PATH / "link-to-python3121-embeddable-package.txt"
BUILD_DIR_PATH = RELEASE_DIR_PATH / "build"
DIST_DIR_PATH = BUILD_DIR_PATH / "pytrnsys"
SITE_PACKAGES_DIR_PATH = DIST_DIR_PATH / "site-packages"


def createRelease() -> None:
    if BUILD_DIR_PATH.is_dir():
        _sh.rmtree(BUILD_DIR_PATH)

    BUILD_DIR_PATH.mkdir()

    embeddablePythonDistDirPath = _downloadAndExtractEmbeddablePythonDist()

    _copyTkTclLibsToEmbeddablePythonDistDir(embeddablePythonDistDirPath)

    _installPackages(embeddablePythonDistDirPath)

    _copyOverBatchScriptsAndReadmeFiles()

    _createReleaseZipFile()


def _downloadAndExtractEmbeddablePythonDist() -> _pl.Path:
    url = URL_FILE_PATH.read_text()
    embeddableZipFileName = _urlp.urlparse(url).path.split("/")[-1]
    embeddableZipFilePath = BUILD_DIR_PATH / embeddableZipFileName

    response: _htc.HTTPResponse
    with _urlreq.urlopen(url) as response, embeddableZipFilePath.open("bw") as embeddableZipFile:
        embeddableZipFile.write(response.read())

    DIST_DIR_PATH.mkdir()
    embeddablePythonDistDirPath = DIST_DIR_PATH / embeddableZipFilePath.stem

    with _zip.ZipFile(embeddableZipFilePath) as zipFile:
        zipFile.extractall(embeddablePythonDistDirPath)

    return embeddablePythonDistDirPath


def _copyTkTclLibsToEmbeddablePythonDistDir(embeddablePythonDistDirPath) -> None:
    for relativeFileOrDirPathToCopy in RELATIVE_TK_TCL_FILE_OR_DIR_PATHS_TO_COPY:
        absoluteSourceFileOrDirPath = PYTHON_312_DIST_DIR_PATH / relativeFileOrDirPathToCopy
        absoluteTargetFileOrDirPath = embeddablePythonDistDirPath / relativeFileOrDirPathToCopy.name

        if absoluteSourceFileOrDirPath.is_dir():
            _sh.copytree(absoluteSourceFileOrDirPath, absoluteTargetFileOrDirPath)
        else:
            containingDirPath = absoluteTargetFileOrDirPath.parent
            containingDirPath.mkdir(parents=True, exist_ok=True)
            _sh.copy(absoluteSourceFileOrDirPath, absoluteTargetFileOrDirPath)


def _installPackages(embeddablePythonDistDirPath: _pl.Path) -> None:
    SITE_PACKAGES_DIR_PATH.mkdir()

    commands = [
        rf"{_sys.executable} dev-tools\generateGuiClassesFromQtCreatorStudioUiFiles.py",
        rf"{_sys.executable} -m pip install -r requirements\release.txt -t {SITE_PACKAGES_DIR_PATH}",
    ]

    pytrnsysGuiRootDirPath = RELEASE_DIR_PATH.parent
    for command in commands:
        _sp.run(command.split(), check=True, cwd=pytrnsysGuiRootDirPath)

    pthFilePath = RELEASE_DIR_PATH / "python312._pth"
    _sh.copy(pthFilePath, embeddablePythonDistDirPath)


def _copyOverBatchScriptsAndReadmeFiles() -> None:
    fileNames = [
        "pytrnsys.bat",
        "pytrnsys-gui.bat",
        "install-pytrnsys-gui-RUN-AS-ADMIN.bat",
        "README.txt"
    ]
    for fileName in fileNames:
        sourceFilePath = RELEASE_DIR_PATH / fileName
        _sh.copy(sourceFilePath, DIST_DIR_PATH)


def _createReleaseZipFile() -> None:
    pytrnsysReleaseZipFilePath = BUILD_DIR_PATH / "pytrnsys.zip"
    with _zip.ZipFile(pytrnsysReleaseZipFilePath, "w") as zipFile:
        for filePath in DIST_DIR_PATH.rglob("*"):
            relativeFilePath = filePath.relative_to(DIST_DIR_PATH)
            zipFile.write(filePath, relativeFilePath)


if __name__ == "__main__":
    createRelease()
