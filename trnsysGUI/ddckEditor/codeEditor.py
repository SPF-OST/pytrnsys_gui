import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtWidgets as _qtw

from . import placeholders as _ph

_CURRENT_LINE_COLOR = "#f2f6fc"
_PROBLEM_LINE_COLOR = "#ffe3e3"
_LINE_NUMBER_BACKGROUND_COLOR = "#f0f0f0"
_LINE_NUMBER_COLOR = "#8c8c8c"
_PROBLEM_LINE_NUMBER_COLOR = "#cf222e"

_TAB_WIDTH_IN_SPACES = 4


class CodeEditor(_qtw.QPlainTextEdit):
    """Plain text editor with line numbers, current-line and problem
    highlighting, and placeholder tooltips.

    The main window has single-key (`a`, `q`) and Ctrl shortcuts for the
    diagram (Ctrl+S, Ctrl+Z, ...). While this editor has focus, typing and
    the editing shortcuts go to the editor instead.
    """

    saveRequested = _qtc.pyqtSignal()
    findRequested = _qtc.pyqtSignal()
    closeRequested = _qtc.pyqtSignal()

    def __init__(self, parent: _qtw.QWidget | None = None) -> None:
        super().__init__(parent)

        self._lineNumberArea = _LineNumberArea(self)
        self._problemsByLineNumber: dict[int, str] = {}
        self._valuesByPort: _ph.ValuesByPort | None = None

        font = _qtg.QFont("Consolas", 10)
        font.setStyleHint(_qtg.QFont.Monospace)
        font.setFixedPitch(True)
        self.setFont(font)
        self.setTabStopDistance(
            _qtg.QFontMetricsF(font).horizontalAdvance(" ")
            * _TAB_WIDTH_IN_SPACES
        )
        self.setLineWrapMode(_qtw.QPlainTextEdit.NoWrap)

        self.blockCountChanged.connect(self._updateLineNumberAreaWidth)
        self.updateRequest.connect(self._updateLineNumberArea)
        self.cursorPositionChanged.connect(self._updateExtraSelections)

        self._updateLineNumberAreaWidth()
        self._updateExtraSelections()

    # Problems and placeholders

    def setProblems(self, problemsByLineNumber: _tp.Mapping[int, str]) -> None:
        self._problemsByLineNumber = dict(problemsByLineNumber)
        self._updateExtraSelections()
        self._lineNumberArea.update()

    def setPlaceholderValues(
        self, valuesByPort: _ph.ValuesByPort | None
    ) -> None:
        self._valuesByPort = valuesByPort

    def goToLine(self, lineNumber: int) -> None:
        block = self.document().findBlockByNumber(lineNumber - 1)
        if not block.isValid():
            return
        cursor = _qtg.QTextCursor(block)
        self.setTextCursor(cursor)
        self.centerCursor()
        self.setFocus()

    # Keyboard handling

    def event(self, event: _qtc.QEvent) -> bool:
        if event.type() == _qtc.QEvent.ShortcutOverride and self._isOwnKey(
            _tp.cast(_qtg.QKeyEvent, event)
        ):
            event.accept()
            return True
        return super().event(event)

    def keyPressEvent(
        self, event: _qtg.QKeyEvent
    ) -> None:  # pylint: disable=invalid-name
        if event.matches(_qtg.QKeySequence.Save):
            self.saveRequested.emit()
            return
        if event.matches(_qtg.QKeySequence.Find) or event.matches(
            _qtg.QKeySequence.Replace
        ):
            self.findRequested.emit()
            return
        if event.matches(_qtg.QKeySequence.Close):
            self.closeRequested.emit()
            return
        super().keyPressEvent(event)

    @staticmethod
    def _isOwnKey(event: _qtg.QKeyEvent) -> bool:
        modifiers = event.modifiers() & ~_qtc.Qt.KeypadModifier
        isPlainTyping = not modifiers & (
            _qtc.Qt.ControlModifier | _qtc.Qt.AltModifier
        )
        if isPlainTyping:
            return True

        ownKeySequences = [
            _qtg.QKeySequence.Save,
            _qtg.QKeySequence.Find,
            _qtg.QKeySequence.Replace,
            _qtg.QKeySequence.Close,
            _qtg.QKeySequence.Undo,
            _qtg.QKeySequence.Redo,
            _qtg.QKeySequence.Copy,
            _qtg.QKeySequence.Cut,
            _qtg.QKeySequence.Paste,
            _qtg.QKeySequence.SelectAll,
        ]
        if any(event.matches(sequence) for sequence in ownKeySequences):
            return True

        # Word-wise navigation and deletion (Ctrl+Left, Ctrl+Backspace, ...)
        navigationKeys = {
            _qtc.Qt.Key_Left,
            _qtc.Qt.Key_Right,
            _qtc.Qt.Key_Up,
            _qtc.Qt.Key_Down,
            _qtc.Qt.Key_Home,
            _qtc.Qt.Key_End,
            _qtc.Qt.Key_Backspace,
            _qtc.Qt.Key_Delete,
        }
        return event.key() in navigationKeys

    # Tooltips

    def viewportEvent(
        self, event: _qtc.QEvent
    ) -> bool:  # pylint: disable=invalid-name
        if event.type() == _qtc.QEvent.ToolTip:
            helpEvent = _tp.cast(_qtg.QHelpEvent, event)
            toolTip = self._getToolTipAt(helpEvent.pos())
            if toolTip:
                _qtw.QToolTip.showText(helpEvent.globalPos(), toolTip, self)
            else:
                _qtw.QToolTip.hideText()
                event.ignore()
            return True
        return super().viewportEvent(event)

    def _getToolTipAt(self, position: _qtc.QPoint) -> str | None:
        cursor = self.cursorForPosition(position)
        block = cursor.block()
        placeholder = _ph.findPlaceholderAt(
            block.text(), cursor.positionInBlock()
        )
        if placeholder:
            return _ph.describe(placeholder, self._valuesByPort)

        return self._problemsByLineNumber.get(block.blockNumber() + 1)

    # Line numbers and extra selections

    def lineNumberAreaWidth(self) -> int:  # pylint: disable=invalid-name
        digits = len(str(max(1, self.blockCount())))
        padding = 12
        return padding + self.fontMetrics().horizontalAdvance("9") * digits

    def resizeEvent(
        self, event: _qtg.QResizeEvent
    ) -> None:  # pylint: disable=invalid-name
        super().resizeEvent(event)
        contents = self.contentsRect()
        self._lineNumberArea.setGeometry(
            _qtc.QRect(
                contents.left(),
                contents.top(),
                self.lineNumberAreaWidth(),
                contents.height(),
            )
        )

    def paintLineNumberArea(
        self, event: _qtg.QPaintEvent
    ) -> None:  # pylint: disable=invalid-name
        painter = _qtg.QPainter(self._lineNumberArea)
        painter.fillRect(
            event.rect(), _qtg.QColor(_LINE_NUMBER_BACKGROUND_COLOR)
        )

        block = self.firstVisibleBlock()
        top = round(
            self.blockBoundingGeometry(block)
            .translated(self.contentOffset())
            .top()
        )
        bottom = top + round(self.blockBoundingRect(block).height())
        width = self._lineNumberArea.width() - 6
        height = self.fontMetrics().height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                lineNumber = block.blockNumber() + 1
                hasProblem = lineNumber in self._problemsByLineNumber
                color = (
                    _PROBLEM_LINE_NUMBER_COLOR
                    if hasProblem
                    else _LINE_NUMBER_COLOR
                )
                painter.setPen(_qtg.QColor(color))
                font = painter.font()
                font.setBold(hasProblem)
                painter.setFont(font)
                painter.drawText(
                    0,
                    top,
                    width,
                    height,
                    _qtc.Qt.AlignRight,
                    str(lineNumber),
                )

            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())

    def _updateLineNumberAreaWidth(self) -> None:
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def _updateLineNumberArea(self, rect: _qtc.QRect, dy: int) -> None:
        if dy:
            self._lineNumberArea.scroll(0, dy)
        else:
            self._lineNumberArea.update(
                0, rect.y(), self._lineNumberArea.width(), rect.height()
            )

        if rect.contains(self.viewport().rect()):
            self._updateLineNumberAreaWidth()

    def _updateExtraSelections(self) -> None:
        selections = []

        for lineNumber in self._problemsByLineNumber:
            block = self.document().findBlockByNumber(lineNumber - 1)
            if not block.isValid():
                continue
            selections.append(
                self._createFullLineSelection(block, _PROBLEM_LINE_COLOR)
            )

        currentBlock = self.textCursor().block()
        if currentBlock.blockNumber() + 1 not in self._problemsByLineNumber:
            selections.append(
                self._createFullLineSelection(
                    currentBlock, _CURRENT_LINE_COLOR
                )
            )

        self.setExtraSelections(selections)

    @staticmethod
    def _createFullLineSelection(
        block: _qtg.QTextBlock, color: str
    ) -> _qtw.QTextEdit.ExtraSelection:
        selection = _qtw.QTextEdit.ExtraSelection()
        selection.format.setBackground(_qtg.QColor(color))
        selection.format.setProperty(_qtg.QTextFormat.FullWidthSelection, True)
        selection.cursor = _qtg.QTextCursor(block)
        selection.cursor.clearSelection()
        return selection


class _LineNumberArea(_qtw.QWidget):
    def __init__(self, editor: CodeEditor) -> None:
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> _qtc.QSize:  # pylint: disable=invalid-name
        return _qtc.QSize(self._editor.lineNumberAreaWidth(), 0)

    def paintEvent(
        self, event: _qtg.QPaintEvent
    ) -> None:  # pylint: disable=invalid-name
        self._editor.paintLineNumberArea(event)
