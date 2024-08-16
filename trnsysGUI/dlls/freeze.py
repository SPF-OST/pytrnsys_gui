import collections.abc as _cabc
import pathlib as _pl

import pytrnsys.utils.result as _res
import pytrnsys.utils.warnings as _warn

import trnsysGUI.common as _com

from . import _regexes


def getUsedDllRelativePaths(logFileContent: str) -> _res.Result[_warn.ValueWithWarnings[_cabc.Sequence[_pl.Path]]]:
    notFoundTypeNumbers = _getNotFoundTypeNumbers(logFileContent)

    if notFoundTypeNumbers:
        sortedNotFoundTypeNumbers = sorted(notFoundTypeNumbers)
        formattedTypeNumbers = "\n".join(f"    {n}" for n in sortedNotFoundTypeNumbers)
        message = f"No DLLs implementing the following types were found:\n\n{formattedTypeNumbers}\n\n"
        return _res.Error(message)

    chosenPathsByTypeNumber = _getChosenFoundPathsByTypeNumber(logFileContent)

    warning = _getDuplicatesWarningOrNone(logFileContent, chosenPathsByTypeNumber)

    uniqueChosenPaths = set(chosenPathsByTypeNumber.values())
    sortedUniqueChosenPaths = _sortPaths(uniqueChosenPaths)
    valueWithWarning = _warn.ValueWithWarnings.create(sortedUniqueChosenPaths, warning)

    return valueWithWarning


def _getNotFoundTypeNumbers(logFileContent: str) -> _cabc.Sequence[int]:
    notFoundTypeNumbers = []
    for match in _regexes.TYPE_NOT_FOUND.finditer(logFileContent):
        group = match.group("type")
        typeNumber = int(group)
        notFoundTypeNumbers.append(typeNumber)

    return notFoundTypeNumbers


def _getChosenFoundPathsByTypeNumber(logFileContent: str) -> _cabc.Mapping[int, _pl.Path]:
    chosenFoundPathsByTypeNumber = {}
    for match in _regexes.TYPES_FOUND.finditer(logFileContent):
        typeNumbers = _regexes.getTypeNumbers(match)
        chosenPath = _regexes.getPath(match)

        for typeNumber in typeNumbers:
            chosenFoundPathsByTypeNumber[typeNumber] = chosenPath

    return chosenFoundPathsByTypeNumber


def _getDuplicatesWarningOrNone(
    logFileContent: str, chosenPathByTypeNumber: _cabc.Mapping[int, _pl.Path]
) -> str | None:
    duplicatePathsByTypeNumber = _getDuplicatePathsByTypeNumber(logFileContent)

    def getTypeNumber(typeNumberAndDuplicatePaths: tuple[int, _cabc.Sequence[_pl.Path]]) -> int:
        return typeNumberAndDuplicatePaths[0]

    typeNumbersAndDuplicatePaths = sorted(duplicatePathsByTypeNumber.items(), key=getTypeNumber)

    messages = []
    for typeNumber, duplicatePaths in typeNumbersAndDuplicatePaths:
        chosenPath = chosenPathByTypeNumber[typeNumber]
        message = _createDuplicateImplementationsMessage(typeNumber, chosenPath, duplicatePaths)
        messages.append(message)

    warning = None
    if messages:
        formattedMessages = "\n\n".join(m for m in messages)
        warning = f"""\
Multiple implementations for the following types were found ("=>" indicates actually
used implementations):

{formattedMessages}
"""

    return warning


def _getDuplicatePathsByTypeNumber(logFileContent: str) -> _cabc.Mapping[int, _cabc.Sequence[_pl.Path]]:
    duplicatePathsByTypeNumber = dict[int, list[_pl.Path]]()
    for match in _regexes.DUPLICATE_FOUND.finditer(logFileContent):
        typeGroup = match.group("type")
        typeNumber = int(typeGroup)

        pathGroup = _regexes.getPath(match)
        relativePath = _pl.Path(pathGroup)

        duplicatePathsForTypeNumber = _com.getOrAdd(typeNumber, list[_pl.Path](), duplicatePathsByTypeNumber)
        duplicatePathsForTypeNumber.append(relativePath)
    return duplicatePathsByTypeNumber


def _createDuplicateImplementationsMessage(
    typeNumber: int, chosenPath: _pl.Path, duplicatePaths: _cabc.Sequence[_pl.Path]
) -> str:
    allPaths = [chosenPath, *duplicatePaths]

    sortedPaths = _sortPaths(allPaths)
    formattedPaths = [f"    {p}" if p != chosenPath else f" => {p}" for p in sortedPaths]
    message = f"Type {typeNumber}:\n{'\n'.join(formattedPaths)}"

    return message


def _sortPaths(paths: _cabc.Iterable[_pl.Path]) -> _cabc.Sequence[_pl.Path]:
    def getPathKey(path: _pl.Path) -> str:
        return str(path.with_suffix("")).casefold()

    sortedPaths = sorted(paths, key=getPathKey)
    return sortedPaths
