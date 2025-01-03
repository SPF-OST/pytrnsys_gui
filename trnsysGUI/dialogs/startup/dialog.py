import pathlib as _pl

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtWidgets as _qtw

import trnsysGUI.common.cancelled as _ccl
import trnsysGUI.constants as _consts
import trnsysGUI.dialogs as _dlgs
import trnsysGUI.recentProjectsHandler as _rph

_dlgs.assertThatLocalGeneratedUIModuleAndResourcesExist(__name__)

import trnsysGUI.dialogs.startup._UI_dialog_generated as _gen  # type: ignore[import]  # pylint: disable=wrong-import-position


class StartupDialog(_qtw.QDialog, _gen.Ui_startupDialog):
    signal: _ccl.MaybeCancelled[_consts.CreateNewOrOpenExisting | _pl.Path]

    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)
        self.buttonGroup.buttonClicked.connect(self.clickButtonHandler)
        # ===============================================================================
        # Must be monospaced font to ensure paths align nicely.
        self.listWidget.setFont(_qtg.QFont(_consts.DEFAULT_MONOSPACED_FONT))
        # ===============================================================================
        self.listWidget.itemDoubleClicked.connect(self.clickButtonHandler)
        _rph.RecentProjectsHandler.initWithExistingRecentProjects()
        maxLength = _rph.RecentProjectsHandler.getLengthOfLongestFileName()
        for recentProject in _rph.RecentProjectsHandler.recentProjects:
            # Padding name to the longest name to nicely align paths.
            formattedFileName = recentProject.stem.ljust(maxLength)
            _qtw.QListWidgetItem(
                f"{formattedFileName} {recentProject}", self.listWidget
            ).setData(_qtc.Qt.UserRole, recentProject)
        self.adjustSizeToContent()

    def clickButtonHandler(self, clickedItem):
        if clickedItem is self.cancelButton:
            self.signal = _ccl.CANCELLED
        if clickedItem is self.createButton:
            self.signal = _consts.CreateNewOrOpenExisting.CREATE_NEW
        if clickedItem is self.openButton:
            self.signal = _consts.CreateNewOrOpenExisting.OPEN_EXISTING
        if isinstance(clickedItem, _qtw.QListWidgetItem):
            self.signal = clickedItem.data(_qtc.Qt.UserRole)
        self.close()

    def adjustSizeToContent(self):
        totalHeight = sum(
            self.listWidget.sizeHintForRow(i)
            for i in range(self.listWidget.count())
        )
        maxWidth = max(
            (
                self.listWidget.fontMetrics().width(
                    self.listWidget.item(i).text()
                )
                for i in range(self.listWidget.count())
            ),
            default=0,
        )

        if totalHeight <= 115 and maxWidth <= self.width():
            # Corresponds to minimum size of dialog.
            return

        if totalHeight > 115:
            self.listWidget.setFixedHeight(
                totalHeight + 2 * self.listWidget.frameWidth()
            )

        if maxWidth > self.width():
            self.listWidget.setFixedWidth(
                maxWidth + 2 * self.listWidget.frameWidth() + 20
            )

    @staticmethod
    def showDialogAndGetResult() -> (
        _ccl.MaybeCancelled[_consts.CreateNewOrOpenExisting | _pl.Path]
    ):
        dialog = StartupDialog()
        dialog.exec()
        return dialog.signal
