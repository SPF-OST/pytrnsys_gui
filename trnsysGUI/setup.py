import pathlib as _pl
import re as _re
import subprocess as _sp
import typing as _tp
import dataclasses as _dc


import pkg_resources  # type: ignore[import]

import pytrnsys.utils.result as _res

_BASE_DIRECTORY = _pl.Path(__file__).parents[1]


@_dc.dataclass(frozen=True, order=True)
class _VersionedPackage:
    name: str = _dc.field(compare=False)
    canonicalName: str
    version: str

    _VERSIONED_PACKAGE_REGEX = _re.compile(r"^([^#\s=]+)==([^#\s=]+)$")

    @classmethod
    def create(cls, serializedVersionedPackage: str) -> "_VersionedPackage":
        match = cls._VERSIONED_PACKAGE_REGEX.match(serializedVersionedPackage)
        if not match:
            raise ValueError(f"Not a package version specification: {serializedVersionedPackage}")

        name = match.group(1)
        version = match.group(2)

        canonicalName = cls._getCanonicalPipPackageName(name)

        return _VersionedPackage(name, canonicalName, version)

    @staticmethod
    def _getCanonicalPipPackageName(name) -> str:
        return _re.sub(r"[\-_.]+", "_", name).lower()

    def __str__(self):
        return f"{self.name}=={self.version}"


def setup() -> _res.Result[None]:
    localVersionPart = pkg_resources.get_distribution("pytrnsys-gui").parsed_version.local
    isDeveloperInstall = localVersionPart and localVersionPart.endswith("dev")
    if isDeveloperInstall:
        result = _checkRequirements()
        if _res.isError(result):
            return _res.error(result)

        _generateCodeFromQtCreatorUiFiles()

    return None


def _checkRequirements() -> _res.Result[None]:
    release3rdPartyTxtFilePath = _BASE_DIRECTORY / "requirements" / "release-3rd-party.txt"

    requiredVersions = _getRequiredVersions(release3rdPartyTxtFilePath)

    installedVersions = _getInstalledNonEditableVersions()

    missingVersions = requiredVersions - installedVersions
    if missingVersions:
        formattedMissingVersions = "\n".join(f"\t{v}" for v in sorted(missingVersions))
        errorMessage = f"""\
The following packages are required but not installed:
{formattedMissingVersions}

Probably the file {release3rdPartyTxtFilePath} was changed by
someone else on GitHub. Consider re-running (don't forget to
activate your virtual environment first)

    `python -m pip install requirements\\dev.txt`

(or

    `python -m piptools sync requirements\\dev.txt`
    
if you're using `pip-tools` [if you don't know what that means 
use the command just above])

followed by

    `python setup.py egg_info -b dev`
"""
        return _res.Error(errorMessage)

    return None


def _getInstalledNonEditableVersions() -> _tp.Set[_VersionedPackage]:
    completedPipFreezeProcess = _sp.run("pip freeze".split(), capture_output=True, text=True, check=True)
    serializedInstalledVersions = completedPipFreezeProcess.stdout.split("\n")
    serializedNonEditableInstalledVersions = [
        v
        for v in serializedInstalledVersions
        if v.strip() and not v.startswith("-e")
    ]
    installedVersions = {_VersionedPackage.create(v) for v in serializedNonEditableInstalledVersions}
    return installedVersions


def _getRequiredVersions(release3rdPartyTxtFilePath: _pl.Path) -> _tp.Set[_VersionedPackage]:
    lines = release3rdPartyTxtFilePath.read_text().split()

    requiredVersions = set()
    for line in lines:
        try:
            requiredVersion = _VersionedPackage.create(line)
        except ValueError:
            continue

        requiredVersions.add(requiredVersion)
    return requiredVersions


def _generateCodeFromQtCreatorUiFiles():
    uiGenerateFilePath = (
        _pl.Path(__file__).parent.parent / "dev-tools" / "generateGuiClassesFromQtCreatorStudioUiFiles.py"
    )
    cmd = ["python.exe", uiGenerateFilePath]
    _sp.run(cmd, check=True)
