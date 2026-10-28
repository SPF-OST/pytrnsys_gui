import dataclasses as _dc
import pathlib as _pl
import re as _re
import subprocess as _sp
import sys as _sys
import typing as _tp

import pytrnsys.utils.result as _res

# The directory containing the `trnsysGUI` package: the checkout in a developer
# install, `site-packages` in a release.
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
            raise ValueError(
                f'Not a package version specification: "{serializedVersionedPackage}"'
            )

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
    if not _isDeveloperInstall():
        return None

    requirementsResult = _checkRequirements()
    if _res.isError(requirementsResult):
        return _res.error(requirementsResult)

    _generateCodeFromQtCreatorUiFiles()

    return None


def _isDeveloperInstall() -> bool:
    # The only use of `_BASE_DIRECTORY` outside developer installs, where it may
    # not be on the file system (e.g. if `trnsysGUI` is loaded from a zip file):
    # `exists()` then simply returns `False`.
    return (_BASE_DIRECTORY / ".git").exists()


def _checkRequirements() -> _res.Result[None]:
    release3rdPartyTxtFilePath = (
        _BASE_DIRECTORY / "requirements" / "release-3rd-party.txt"
    )

    requiredVersions = _getRequiredVersions(release3rdPartyTxtFilePath)

    result = _getInstalledNonEditableVersions()
    if _res.isError(result):
        return _res.error(result)
    installedVersions = _res.value(result)

    missingVersions = requiredVersions - installedVersions
    if missingVersions:
        formattedMissingVersions = "\n".join(
            f"\t{v}" for v in sorted(missingVersions)
        )
        errorMessage = f"""\
The following packages are required but not installed:
{formattedMissingVersions}

Probably the file {release3rdPartyTxtFilePath} was changed by
someone else on GitHub. Consider re-running (don't forget to
activate your virtual environment first)

    `python -m uv pip install -r requirements\\dev.txt`

(or

    `python -m uv pip sync requirements\\dev.txt`

to also remove packages not listed in `dev.txt`).
"""
        return _res.Error(errorMessage)

    return None


def _getInstalledNonEditableVersions() -> (
    _res.Result[_tp.Set[_VersionedPackage]]
):
    args = [_sys.executable, "-m", "pip", "freeze", "--no-color"]
    completedPipFreezeProcess = _sp.run(
        args, capture_output=True, text=True, check=True
    )
    serializedInstalledVersions = completedPipFreezeProcess.stdout.split("\n")
    serializedNonEditableInstalledVersions = [
        v
        for v in serializedInstalledVersions
        if v.strip() and not v.startswith("-e")
    ]
    try:
        installedVersions = {
            _VersionedPackage.create(v)
            for v in serializedNonEditableInstalledVersions
        }
    except ValueError as valueError:
        errorMessage = f"""\
Could not parse `pip` freeze output:

    {valueError}

Please try updating `pip` from within your virtual environment like so:

    (venv) C:\\...\\pytrnsys_gui> python -m pip install --upgrade pip==22.3.1
"""
        return _res.Error(errorMessage)

    return installedVersions


def _getRequiredVersions(
    release3rdPartyTxtFilePath: _pl.Path,
) -> _tp.Set[_VersionedPackage]:
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
        _BASE_DIRECTORY
        / "dev-tools"
        / "generateGuiClassesFromQtCreatorStudioUiFiles.py"
    )
    cmd = [_sys.executable, uiGenerateFilePath]
    _sp.run(cmd, check=True)
