import pathlib as _pl
import subprocess as _sp
import typing as _tp


def getUntrackedRelativePaths(
    projectFolderPathUnderVersionControl: _pl.Path,
) -> _tp.Sequence[_pl.Path]:
    untrackedPathsRelativeToRepoRoot = _getUntrackedPathsRelativeToRepoRoot(
        projectFolderPathUnderVersionControl
    )

    repositoryRootDirPath = _getRepositoryRootDirPath()

    untrackedAbsolutePaths = [
        repositoryRootDirPath / p for p in untrackedPathsRelativeToRepoRoot
    ]

    untrackedRelativePaths = [
        p.relative_to(projectFolderPathUnderVersionControl)
        for p in untrackedAbsolutePaths
    ]

    return untrackedRelativePaths


def _getRepositoryRootDirPath() -> _pl.Path:
    completedProcess = _sp.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        text=True,
        capture_output=True,
    )

    repositoryRootDirPath = completedProcess.stdout.splitlines()[0]

    return _pl.Path(repositoryRootDirPath)


def _getUntrackedPathsRelativeToRepoRoot(
    projectFolderPathUnderVersionControl: _pl.Path,
) -> _tp.Sequence[_pl.Path]:
    completedProcess = _sp.run(
        [
            "git",
            "status",
            "-unormal",
            "--porcelain",
            str(projectFolderPathUnderVersionControl),
        ],
        check=True,
        text=True,
        capture_output=True,
    )

    statusesAndUntrackedPath = completedProcess.stdout.splitlines()

    untrackedPaths = []
    for statusAndUntrackedPath in statusesAndUntrackedPath:
        status, untrackedPathAsString = statusAndUntrackedPath.split()

        untrackedStatus = "??"
        if status != untrackedStatus:
            continue

        untrackedPath = _pl.Path(untrackedPathAsString)

        untrackedPaths.append(untrackedPath)

    return untrackedPaths
