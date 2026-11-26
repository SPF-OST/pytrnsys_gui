import re as _re
import typing as _tp

import PyQt5.QtGui as _qtg

from . import placeholders as _ph


def _createFormat(
    color: str,
    bold: bool = False,
    italic: bool = False,
    background: str | None = None,
) -> _qtg.QTextCharFormat:
    charFormat = _qtg.QTextCharFormat()
    charFormat.setForeground(_qtg.QColor(color))
    if bold:
        charFormat.setFontWeight(_qtg.QFont.Bold)
    if italic:
        charFormat.setFontItalic(True)
    if background:
        charFormat.setBackground(_qtg.QColor(background))
    return charFormat


_KEYWORDS = [
    "EQUATIONS",
    "CONSTANTS",
    "PARAMETERS",
    "INPUTS",
    "DERIVATIVES",
    "LABELS",
    "TRACE",
    "ASSIGN",
    "SIMULATION",
    "TOLERANCES",
    "LIMITS",
    "NAN_CHECK",
    "OVERWRITE_CHECK",
    "TIME_REPORT",
    "DFQ",
    "EQSOLVER",
    "SOLVER",
    "END",
    "WIDTH",
    "LIST",
    "NOLIST",
    "ETRACE",
    "VERSION",
    "ACCELERATE",
    "CONST",
]

_Rule = _tp.Tuple[_re.Pattern, _qtg.QTextCharFormat]

_RULES: _tp.Sequence[_Rule] = [
    # Numbers (but not digits that are part of names like `Tes1`).
    (
        _re.compile(r"(?<![\w.])[+-]?\d+(\.\d*)?([eE][+-]?\d+)?\b"),
        _createFormat("#b35900"),
    ),
    # Outputs of other units, e.g. `[50,1]`.
    (_re.compile(r"\[\s*\d+\s*,\s*\d+\s*\]"), _createFormat("#00808a")),
    # Local (`:name`) and global (`$name`) variables.
    (_re.compile(r"[:$][A-Za-z]\w*"), _createFormat("#6a3d9a", italic=True)),
    (
        _re.compile(r"\b(" + "|".join(_KEYWORDS) + r")\b", _re.IGNORECASE),
        _createFormat("#0033b3", bold=True),
    ),
    (
        _re.compile(r"\b(UNIT|TYPE)\b", _re.IGNORECASE),
        _createFormat("#9e0f8f", bold=True),
    ),
]

_COMMENT_FORMAT = _createFormat("#8c8c8c", italic=True)

_RESOLVED_PLACEHOLDER_FORMAT = _createFormat(
    "#1a7f37", bold=True, background="#e6f4ea"
)
_UNKNOWN_PLACEHOLDER_FORMAT = _createFormat(
    "#9a6700", bold=True, background="#fff8c5"
)
_UNRESOLVED_PLACEHOLDER_FORMAT = _createFormat(
    "#cf222e", bold=True, background="#ffebe9"
)
_UNRESOLVED_PLACEHOLDER_FORMAT.setUnderlineStyle(
    _qtg.QTextCharFormat.WaveUnderline
)
_UNRESOLVED_PLACEHOLDER_FORMAT.setUnderlineColor(_qtg.QColor("#cf222e"))


class DdckHighlighter(_qtg.QSyntaxHighlighter):
    """Syntax highlighting for TRNSYS deck files (ddck/dck).

    Placeholders (`@temp(In)`, ...) are colored green if the diagram
    resolves them, red if it can't and yellow if it's unknown (diagram not
    fully connected, or the file doesn't belong to a component).
    """

    def __init__(self, document: _qtg.QTextDocument) -> None:
        super().__init__(document)
        self._valuesByPort: _ph.ValuesByPort | None = None

    def setPlaceholderValues(
        self, valuesByPort: _ph.ValuesByPort | None
    ) -> None:
        self._valuesByPort = valuesByPort
        self.rehighlight()

    def highlightBlock(
        self, text: str
    ) -> None:  # pylint: disable=invalid-name
        for regex, charFormat in _RULES:
            for match in regex.finditer(text):
                self.setFormat(
                    match.start(), match.end() - match.start(), charFormat
                )

        for placeholder in _ph.findPlaceholders(text):
            self.setFormat(
                placeholder.start,
                placeholder.end - placeholder.start,
                self._getPlaceholderFormat(placeholder),
            )

        self._highlightComments(text)

    def _getPlaceholderFormat(
        self, placeholder: _ph.PlaceholderMatch
    ) -> _qtg.QTextCharFormat:
        if not placeholder.isHydraulic or self._valuesByPort is None:
            return _UNKNOWN_PLACEHOLDER_FORMAT

        if _ph.isUnresolved(placeholder, self._valuesByPort):
            return _UNRESOLVED_PLACEHOLDER_FORMAT

        return _RESOLVED_PLACEHOLDER_FORMAT

    def _highlightComments(self, text: str) -> None:
        if text.lstrip().startswith("*"):
            self.setFormat(0, len(text), _COMMENT_FORMAT)
            return

        index = text.find("!")
        if index >= 0:
            self.setFormat(index, len(text) - index, _COMMENT_FORMAT)
