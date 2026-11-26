import dataclasses as _dc
import pathlib as _pl
import re as _re
import typing as _tp

import pytrnsys.ddck.replaceTokens.defaultVisibility as _dv
import pytrnsys.ddck.replaceTokens.placeholders as _rtph
import pytrnsys.ddck.replaceTokens.withoutPlaceholders as _rtwph
import pytrnsys.utils.result as _res

from . import placeholders as _ph


@_dc.dataclass(frozen=True)
class Problem:
    lineNumber: int | None  # 1-based, None if unknown
    message: str


# `ReplaceTokenError.getErrorMessage` produces "At <path>:<line>:", lark
# produces "... at line <line> col <col>" or "... at line <line>, column <col>".
_LINE_NUMBER_REGEXES = [
    _re.compile(r"^At .*:(\d+):\s*$", _re.MULTILINE),
    _re.compile(r"\bat line (\d+)", _re.IGNORECASE),
]


def getComponentName(ddckFilePath: _pl.Path) -> str:
    """Component ddcks live in `ddck/<component name>/<file>.ddck`, and that's
    how pytrnsys determines the component name, too."""
    return ddckFilePath.parent.name


def validateDdck(
    content: str,
    componentName: str,
    valuesByPort: _ph.ValuesByPort | None,
    filePath: _pl.Path | None = None,
) -> _tp.Sequence[Problem]:
    """Checks the content the same way pytrnsys does when building the deck.

    If `valuesByPort` is None (diagram not available) the placeholders are
    checked as if no `DdckPlaceHolderValues.json` were used, i.e. they must
    provide defaults.

    pytrnsys stops at the first error, so at most one problem is reported
    from it. Placeholders the diagram can't resolve are additionally reported
    individually, with their line numbers.
    """
    unresolvedProblems = _findUnresolvedPlaceholders(content, valuesByPort)

    pytrnsysProblems = _validateWithPytrnsys(
        content, componentName, valuesByPort, filePath
    )

    # Without a line number, pytrnsys' error is most probably about the
    # unresolved placeholders already reported (with line numbers).
    if unresolvedProblems:
        pytrnsysProblems = [
            p for p in pytrnsysProblems if p.lineNumber is not None
        ]

    return [*unresolvedProblems, *pytrnsysProblems]


def _findUnresolvedPlaceholders(
    content: str, valuesByPort: _ph.ValuesByPort | None
) -> _tp.Sequence[Problem]:
    if valuesByPort is None:
        return []

    problems = []
    for lineNumber, line in enumerate(content.splitlines(), start=1):
        code = stripComment(line)
        for match in _ph.findPlaceholders(code):
            if _ph.isUnresolved(match, valuesByPort):
                message = _ph.describe(match, valuesByPort).replace("\n", " ")
                problems.append(Problem(lineNumber, message))
    return problems


def stripComment(line: str) -> str:
    """Comments are lines starting with `*` or anything after `!`."""
    if line.lstrip().startswith("*"):
        return ""
    return line.split("!", maxsplit=1)[0]


def _validateWithPytrnsys(
    content: str,
    componentName: str,
    valuesByPort: _ph.ValuesByPort | None,
    filePath: _pl.Path | None,
) -> _tp.Sequence[Problem]:
    if valuesByPort is None:
        result = _rtwph.replaceTokensWithDefaultsInString(
            content, componentName, _dv.DefaultVisibility.LOCAL, filePath
        )
    else:
        result = _rtph.replaceTokensInString(
            content,
            componentName,
            valuesByPort,
            _dv.DefaultVisibility.LOCAL,
            filePath,
        )

    if not _res.isError(result):
        return []

    message = _res.error(result).message
    return [Problem(_extractLineNumber(message), message)]


def _extractLineNumber(message: str) -> int | None:
    for regex in _LINE_NUMBER_REGEXES:
        match = regex.search(message)
        if match:
            return int(match.group(1))
    return None
