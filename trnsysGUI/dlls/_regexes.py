import collections.abc as _cabc
import pathlib as _pl
import re as _re

from . import _patterns

TYPES_FOUND = _re.compile(_patterns.TYPES_FOUND, _re.MULTILINE)
DUPLICATE_FOUND = _re.compile(_patterns.DUPLICATE_FOUND, _re.MULTILINE)
TYPE_NOT_FOUND = _re.compile(_patterns.TYPE_NOT_FOUND, _re.MULTILINE)


def getPath(match: _re.Match[str]) -> _pl.Path:
    group = match["quotedPath"]

    if group is None:
        group = match["path"]

    if group is None:
        raise ValueError("Match doesn't contain a path.", match)

    path = _pl.Path(group)

    return path


def getTypeNumbers(match: _re.Match[str]) -> _cabc.Sequence[int]:
    typeGroup = match["type"]
    typeNumber = _getTypeNumber(typeGroup)
    typeNumbers = [typeNumber]

    moreTypesGroup = match["moreTypes"]
    if moreTypesGroup:
        moreTypeGroups = moreTypesGroup.removeprefix(", ").split(", ")
        moreTypeNumbers = [_getTypeNumber(n) for n in moreTypeGroups]
        typeNumbers.extend(moreTypeNumbers)

    return typeNumbers


def _getTypeNumber(typeGroup: str) -> int:
    typeNumber = int(typeGroup.lower().removeprefix("type"))
    return typeNumber
