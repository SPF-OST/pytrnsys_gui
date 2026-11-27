"""After renaming a component: lets the user choose which config lines with
identifiers prefixed with the old name (`deck CollNbModTot 360`) get the new
name."""

import html as _html
import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtWidgets as _qtw

import trnsysGUI.runConfig as _rc


class PrefixedIdentifiersDialog(_qtw.QDialog):
    def __init__(
        self,
        oldName: str,
        newName: str,
        lines: _tp.Sequence[_rc.PrefixedIdentifiersLine],
        parent: _qtw.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Rename parameters?")
        self.resize(750, 420)
        self._lines = list(lines)

        explanation = _qtw.QLabel(
            f"pytrnsys prefixes the local variables of a component's ddcks"
            f" with its name. These lines of the config use names starting"
            f" with <b>{_html.escape(oldName)}</b>: rename them to start with"
            f" <b>{_html.escape(newName)}</b>?<br>Lines in the component's"
            " block are checked; check the others only if they refer to this"
            " component."
        )
        explanation.setWordWrap(True)

        self._list = _qtw.QListWidget()
        for line in self._lines:
            location = "block" if line.isInComponentBlock else "elsewhere"
            item = _qtw.QListWidgetItem(
                f"{line.lineIndex + 1}: {line.line.strip()}"
                f"   →   {line.newLine.strip()}   ({location})"
            )
            item.setFlags(item.flags() | _qtc.Qt.ItemIsUserCheckable)
            item.setCheckState(
                _qtc.Qt.Checked
                if line.isInComponentBlock
                else _qtc.Qt.Unchecked
            )
            self._list.addItem(item)

        buttonBox = _qtw.QDialogButtonBox()
        buttonBox.addButton("Rename checked", _qtw.QDialogButtonBox.AcceptRole)
        buttonBox.addButton("Don't rename", _qtw.QDialogButtonBox.RejectRole)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = _qtw.QVBoxLayout(self)
        layout.addWidget(explanation)
        layout.addWidget(self._list, 1)
        layout.addWidget(buttonBox)

    def getCheckedLines(self) -> _tp.Sequence[_rc.PrefixedIdentifiersLine]:
        checked = []
        for index, line in enumerate(self._lines):
            item = self._list.item(index)
            if item and item.checkState() == _qtc.Qt.Checked:
                checked.append(line)
        return checked

    def setAllChecked(self, isChecked: bool) -> None:
        for index in range(self._list.count()):
            item = self._list.item(index)
            if item:
                item.setCheckState(
                    _qtc.Qt.Checked if isChecked else _qtc.Qt.Unchecked
                )


def askAndRenamePrefixedIdentifiers(
    config: _rc.RunConfig,
    oldName: str,
    newName: str,
    parent: _qtw.QWidget | None,
) -> int:
    """Shows the dialog if there are such lines and renames the checked
    ones in `config` (not written). Returns the number of changed lines."""
    lines = config.findPrefixedIdentifierLines(oldName, newName)
    if not lines:
        return 0

    dialog = PrefixedIdentifiersDialog(oldName, newName, lines, parent)
    if dialog.exec() != _qtw.QDialog.Accepted:
        return 0

    checkedLines = dialog.getCheckedLines()
    for line in checkedLines:
        config.replaceLine(line.lineIndex, line.line, line.newLine)
    return len(checkedLines)
