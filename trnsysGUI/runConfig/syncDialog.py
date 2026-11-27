"""Shows the result of synchronizing the active config with the project and
lets the user add the project's ddcks that the config doesn't use yet."""

import html as _html
import pathlib as _pl
import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtWidgets as _qtw

from . import sync as _sync

_PATH_ROLE = _qtc.Qt.UserRole


class SyncDialog(_qtw.QDialog):
    def __init__(
        self,
        configFileName: str,
        report: _sync.SyncReport,
        parent: _qtw.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Sync {configFileName}")
        self.resize(650, 450)

        layout = _qtw.QVBoxLayout(self)

        summary = _qtw.QLabel(self._createSummary(configFileName, report))
        summary.setWordWrap(True)
        summary.setTextInteractionFlags(_qtc.Qt.TextSelectableByMouse)
        layout.addWidget(summary)

        self._unusedList = _qtw.QListWidget()
        for relativePath in report.unusedDdckFiles:
            item = _qtw.QListWidgetItem(str(relativePath))
            item.setFlags(item.flags() | _qtc.Qt.ItemIsUserCheckable)
            item.setCheckState(_qtc.Qt.Unchecked)
            item.setData(_PATH_ROLE, str(relativePath))
            self._unusedList.addItem(item)

        buttonBox = _qtw.QDialogButtonBox(_qtw.QDialogButtonBox.Close)
        buttonBox.rejected.connect(self.reject)

        if report.unusedDdckFiles:
            layout.addWidget(
                _qtw.QLabel(
                    "<b>ddcks in the project's ddck folder not used by the"
                    " config</b> (check the ones to add):"
                )
            )
            layout.addWidget(self._unusedList, 1)
            addButton = buttonBox.addButton(
                "Add checked", _qtw.QDialogButtonBox.AcceptRole
            )
            addButton.setToolTip(
                "Added to the block of the component of the same name, or"
                " before the `end` ddck."
            )
            buttonBox.accepted.connect(self.accept)
        else:
            self._unusedList.hide()
            layout.addStretch()

        layout.addWidget(buttonBox)

    def getCheckedDdckFiles(self) -> _tp.Sequence[_pl.PurePosixPath]:
        checked = []
        for index in range(self._unusedList.count()):
            item = self._unusedList.item(index)
            if item and item.checkState() == _qtc.Qt.Checked:
                checked.append(_pl.PurePosixPath(item.data(_PATH_ROLE)))
        return checked

    @staticmethod
    def _createSummary(configFileName: str, report: _sync.SyncReport) -> str:
        parts = [f"<b>{_html.escape(configFileName)}</b>"]

        if report.addedSettings:
            settings = "<br>".join(
                f"<code>{_html.escape(s)}</code>" for s in report.addedSettings
            )
            parts.append(f"Added missing settings:<br>{settings}")
        else:
            parts.append("No settings were missing.")

        if report.brokenIncludes:
            broken = "<br>".join(
                f"<code>{_html.escape(b.line)}</code>: {_html.escape(b.reason)}"
                for b in report.brokenIncludes
            )
            parts.append(
                "<span style='color:#cf222e'><b>ddcks that can't be"
                f" found:</b></span><br>{broken}"
            )
        else:
            parts.append("All ddcks of the config were found.")

        if not report.unusedDdckFiles:
            parts.append("All ddcks of the project's ddck folder are used.")

        return "<br><br>".join(parts)
