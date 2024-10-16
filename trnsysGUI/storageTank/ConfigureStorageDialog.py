# pylint: disable = invalid-name
from __future__ import annotations

import typing as _tp
import pathlib as _pl

import PyQt5.QtCore as _qtc
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QListWidget
from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QRadioButton
from PyQt5.QtWidgets import QSpacerItem
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget

import trnsysGUI.directPortPair as _dpp
import trnsysGUI.hydraulicLoops.split as _hls
import trnsysGUI.modifyRelativeHeightsDialog as _mhd
import trnsysGUI.names.dialog as _ndialog
import trnsysGUI.names.rename as _rename
import trnsysGUI.storageTank.side as _sd

if _tp.TYPE_CHECKING:
    import trnsysGUI.storageTank.widget as _st
    import trnsysGUI.diagram.Editor as _ed


class ConfigureStorageDialog(_ndialog.ChangeNameDialogBase):  # pylint: disable = too-many-instance-attributes
    WIDTH_INCREMENT = 10
    HEIGHT_INCREMENT = 100
    minimumPortDistance = 9

    MISSING_NAME_ERROR_MESSAGE = "Please specify the name of the heat exchanger that you want to add."
    PORT_HEIGHT_ERROR_MESSAGE = (
        "Ports need to be on the tank, please make sure the port heights are within (0 %, 100 %)."
    )
    NO_SIDE_SELECTED_ERROR_MESSAGE = "No side selected for heat exchanger."

    isTest = False

    def __init__(
        self,
        storage: _st.StorageTank,
        editor: _ed.Editor,  # type: ignore[name-defined]
        renameHelper: _rename.RenameHelper,
        projectDirPath: str,
    ) -> None:
        super().__init__(storage, renameHelper, _pl.Path(projectDirPath))
        self._editor = editor
        self.storage = storage
        self.__post_init__()

    def __post_init__(self):  # pylint: disable = too-many-locals, too-many-statements
        spacerHeight = 15

        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()

        self.tabs.addTab(self.tab1, "Heat exchangers")
        self.tabs.addTab(self.tab2, "Direct ports")

        h0 = QHBoxLayout()  # pylint: disable = invalid-name
        description = QLabel("Please configure the storage tank:")
        exportButton = QPushButton("Export ddck")
        exportButton.clicked.connect(self.storage.exportDck)

        h0.addWidget(description)
        h0.addWidget(exportButton)

        tankNameLabel = QLabel()
        tankNameLabel.setText("<b>Tank name: </b>")

        gridLayout = QGridLayout()
        hxsLabel = QLabel("<b>Heat Exchangers </b>")
        gridLayout.addWidget(hxsLabel, 0, 0, 1, 2)

        qhbL = QHBoxLayout()

        self.leftHeatExchangersItemListWidget = QListWidget()
        qhbL.addWidget(self.leftHeatExchangersItemListWidget)

        self.rightHeatExchangersItemListWidget = QListWidget()
        qhbL.addWidget(self.rightHeatExchangersItemListWidget)

        offsetLabel = QLabel("Height offsets in percent")
        offsetLeILabel = QLabel("Input:")
        offsetLeOLabel = QLabel("Output:")
        self.offsetLeI = QLineEdit("0")
        self.offsetLeO = QLineEdit("0")
        self.lButton = QRadioButton("Left side")
        self.rButton = QRadioButton("Right side")

        gridLayout.addWidget(offsetLabel, 3, 0, 1, 1)
        gridLayout.addWidget(offsetLeILabel, 4, 0, 1, 1)
        gridLayout.addWidget(self.offsetLeI, 5, 0, 1, 3)
        gridLayout.addWidget(offsetLeOLabel, 6, 0, 1, 1)
        gridLayout.addWidget(self.offsetLeO, 7, 0, 1, 3)

        self.hxNameLe = QLineEdit()
        self.hxNameLe.setPlaceholderText("Enter a name...")
        gridLayout.addWidget(self.hxNameLe, 8, 0, 1, 3)

        gridLayout.addWidget(self.lButton, 9, 0, 1, 1)
        gridLayout.addWidget(self.rButton, 9, 2, 1, 1)

        self.addButton = QPushButton("Add...")
        self.addButton.clicked.connect(self.addHx)
        gridLayout.addWidget(self.addButton, 10, 0, 1, 1)
        removeButton = QPushButton("Remove...")
        removeButton.clicked.connect(self.removeHxL)
        removeButton.clicked.connect(self.removeHxR)
        gridLayout.addWidget(removeButton, 10, 1, 1, 1)
        modifyButton = QPushButton("Modify")
        modifyButton.clicked.connect(self.modifyHx)
        gridLayout.addWidget(modifyButton, 10, 2, 1, 1)
        spaceHx = QSpacerItem(self.width(), spacerHeight)
        gridLayout.addItem(spaceHx, 11, 0, 1, 2)

        manPortLay = QVBoxLayout()
        qhbL2 = QHBoxLayout()

        self.leftDirectPortPairsItemListWidget = QListWidget()
        qhbL2.addWidget(self.leftDirectPortPairsItemListWidget)

        self.rightDirectPortPairsItemListWidget = QListWidget()
        qhbL2.addWidget(self.rightDirectPortPairsItemListWidget)

        manPortLay.addLayout(qhbL2)

        manPortLabel = QLabel("<b>Set port manually</b>")
        manPortLabel2 = QLabel("Enter height in percent: ")
        portlabelUpper = QLabel("Inlet")
        self.manPortLeI = QLineEdit("0")
        portlabelLower = QLabel("Outlet")
        self.manPortLeO = QLineEdit("0")

        qhbl3 = QHBoxLayout()
        self.manlButton = QRadioButton("Left side")
        self.manrButton = QRadioButton("Right side")
        qhbl3.addWidget(self.manlButton)
        qhbl3.addWidget(self.manrButton)

        self.manAddButton = QPushButton("Add (manual) ports")
        self.manAddButton.clicked.connect(self.addPortPair)

        self.manRemovebutton = QPushButton("Remove ports")
        self.manRemovebutton.clicked.connect(self.removePortPairLeft)
        self.manRemovebutton.clicked.connect(self.removePortPairRight)

        self.modifyPortButton = QPushButton("Modify")
        self.modifyPortButton.clicked.connect(self.modifyPort)

        addRemoveButtons = QHBoxLayout()
        addRemoveButtons.addWidget(self.manAddButton)
        addRemoveButtons.addWidget(self.manRemovebutton)
        addRemoveButtons.addWidget(self.modifyPortButton)

        manPortLay.addWidget(manPortLabel)
        manPortLay.addWidget(manPortLabel2)
        manPortLay.addWidget(portlabelUpper)
        manPortLay.addWidget(self.manPortLeI)
        manPortLay.addWidget(portlabelLower)
        manPortLay.addWidget(self.manPortLeO)
        manPortLay.addLayout(qhbl3)
        manPortLay.addLayout(addRemoveButtons)

        increaseSizeButton = QPushButton("Increase size")
        decreaseSizeButton = QPushButton("Decrease size")
        self.okButton = QPushButton("OK")
        self.cancelButton = QPushButton("Cancel")

        increaseSizeButton.clicked.connect(self.increaseSize)
        decreaseSizeButton.clicked.connect(self.decreaseSize)
        self.okButton.clicked.connect(self.acceptedEdit)
        self.cancelButton.clicked.connect(self.cancel)

        layout = QVBoxLayout()
        layout.addLayout(h0)
        layout.addWidget(tankNameLabel)
        layout.addWidget(self._displayNameLineEdit)

        t1Layout = QVBoxLayout()
        t1Layout.addLayout(qhbL)
        t1Layout.addLayout(gridLayout)

        self.tab1.setLayout(t1Layout)

        self.tab2.setLayout(manPortLay)

        layout.addWidget(self.tabs)

        layout.addWidget(increaseSizeButton)
        layout.addWidget(decreaseSizeButton)
        layout.addWidget(self.okButton)
        layout.addWidget(self.cancelButton)

        self.setLayout(layout)

        self._loadHeatExchangers()
        self._loadDirectPortPairs()

        # This is to ensure that only one list element is selected
        self.rightHeatExchangersItemListWidget.setSelectionMode(QListWidget.SelectionMode(1))
        self.leftHeatExchangersItemListWidget.setSelectionMode(QListWidget.SelectionMode(1))
        self.rightHeatExchangersItemListWidget.clicked.connect(self.listWRClicked)
        self.leftHeatExchangersItemListWidget.clicked.connect(self.listWLClicked)

        self.rightDirectPortPairsItemListWidget.setSelectionMode(QListWidget.SelectionMode(1))
        self.leftDirectPortPairsItemListWidget.setSelectionMode(QListWidget.SelectionMode(1))
        self.rightDirectPortPairsItemListWidget.clicked.connect(self.listWR2Clicked)
        self.leftDirectPortPairsItemListWidget.clicked.connect(self.listWL2Clicked)

        self.msgb = QMessageBox()

        self.show()

    def _loadHeatExchangers(self):
        self.leftHeatExchangersItemListWidget.clear()
        self.rightHeatExchangersItemListWidget.clear()

        for heatExchanger in self.storage.heatExchangers:
            itemText = self._getHeatExchangerListItemText(heatExchanger)
            item = QListWidgetItem(itemText)
            item.setData(_qtc.Qt.UserRole, heatExchanger)

            if heatExchanger.sSide == 0:
                self.leftHeatExchangersItemListWidget.addItem(item)
            else:
                self.rightHeatExchangersItemListWidget.addItem(item)

    @staticmethod
    def _getHeatExchangerListItemText(h):  # pylint: disable = invalid-name
        return (
            f"{h.displayName}, y_offset = {int(h.relativeInputHeight * 100)}% to {int(h.relativeOutputHeight * 100)}%"
        )

    def _loadDirectPortPairs(self):
        self.leftDirectPortPairsItemListWidget.clear()
        self.rightDirectPortPairsItemListWidget.clear()

        directPortPair: _dpp.DirectPortPair
        for directPortPair in self.storage.directPortPairs:
            itemText = self._getDirectPortPairListItemText(directPortPair)
            item = QListWidgetItem(itemText)
            item.setData(_qtc.Qt.UserRole, directPortPair)

            if directPortPair.side.isLeft:
                self.leftDirectPortPairsItemListWidget.addItem(item)
            else:
                self.rightDirectPortPairsItemListWidget.addItem(item)

    @staticmethod
    def _getDirectPortPairListItemText(directPortPair: _dpp.DirectPortPair):
        return (
            f"Port pair from {int(directPortPair.relativeInputHeight * 100)}% to "
            f"{int(directPortPair.relativeOutputHeight * 100)}%"
        )

    def listWLClicked(self):
        self.rightHeatExchangersItemListWidget.clearSelection()

    def listWRClicked(self):
        self.leftHeatExchangersItemListWidget.clearSelection()

    def listWL2Clicked(self):
        self.rightDirectPortPairsItemListWidget.clearSelection()

    def listWR2Clicked(self):
        self.leftDirectPortPairsItemListWidget.clearSelection()

    def addHx(self):
        """
        Checks whether the inputs are in the correct range (0,100) and in order, and calls the function for creating a
        HeatExchanger on the respective side.

        Returns
        -------
        """
        try:
            _inputPercentageHeight = float(self.offsetLeI.text())
        except ValueError:
            self._editor.logger.warning("HX input height is not a number.")
            return

        try:
            _outputPercentageHeight = float(self.offsetLeO.text())
        except ValueError:
            self._editor.logger.warning("HX output height is not a number.")
            return

        if self.minOffsetDistance() and self.offsetsInRange():
            if self.rButton.isChecked():
                self._editor.logger.debug("Adding HX on righthand side.")
                self._addHxR()
            elif self.lButton.isChecked():
                self._editor.logger.debug("Adding HX on lefthand side.")
                self._addHxL()
            else:
                self._editor.logger.warning("No side selected for heat exchanger.")
                return
        else:
            self._openMessageBox(f"At least {self.minimumPortDistance}% of difference needed and valid range (0, 100)")

    def minOffsetDistance(self):
        return abs(float(self.offsetLeI.text()) - float(self.offsetLeO.text())) >= self.minimumPortDistance

    def offsetsInRange(self):
        return (0 <= float(self.offsetLeI.text()) <= 100) and (0 <= float(self.offsetLeO.text()) <= 100)

    def _addHxL(self):
        self._addHeatExchanger(_sd.Side.LEFT)

    def _addHxR(self):
        self._addHeatExchanger(_sd.Side.RIGHT)

    def _addHeatExchanger(self, side: _sd.Side):
        name = self.hxNameLe.text()
        if not name:
            self._openMessageBox(self.MISSING_NAME_ERROR_MESSAGE)
            return

        relativeInputHeight = float(self.offsetLeI.text()) / 100
        relativeOutputHeight = float(self.offsetLeO.text()) / 100

        trnsysId = self._editor.idGen.getTrnsysID()
        self.storage.addHeatExchanger(name, trnsysId, side, relativeInputHeight, relativeOutputHeight)

        self._loadHeatExchangers()

    def addPortPair(self):
        try:
            _inputPortPercentageHeight = float(self.manPortLeI.text())
        except ValueError:
            self._editor.logger.warning("Input port height is not a number.")
            return

        try:
            _outputPortPercentageHeight = float(self.manPortLeO.text())
        except ValueError:
            self._editor.logger.warning("Output port height is not a number.")
            return

        if (
            max(_inputPortPercentageHeight, _outputPortPercentageHeight) >= 100
            or min(_inputPortPercentageHeight, _outputPortPercentageHeight) <= 0
        ):
            self._openMessageBox(self.PORT_HEIGHT_ERROR_MESSAGE)
            return

        trnsysId = self._editor.idGen.getTrnsysID()

        if self.manlButton.isChecked():
            _pairSide = _sd.Side.LEFT
        elif self.manrButton.isChecked():
            _pairSide = _sd.Side.RIGHT
        else:
            self._editor.logger.warning("No side selected for port pair.")
            self._openMessageBox(self.NO_SIDE_SELECTED_ERROR_MESSAGE)
            return

        self.storage.addDirectPortPair(
            trnsysId,
            _pairSide,
            _inputPortPercentageHeight / 100,
            _outputPortPercentageHeight / 100,
            self.storage.h,
        )

        self._loadDirectPortPairs()

    def removePortPairLeft(self):
        self._removeSelectedPortPairs(self.leftDirectPortPairsItemListWidget)

    def removePortPairRight(self):
        self._removeSelectedPortPairs(self.rightDirectPortPairsItemListWidget)

    def _removeSelectedPortPairs(self, directPortPairsListWidget):
        for selectedItem in directPortPairsListWidget.selectedItems():
            selectedDirectPortPair: _dpp.DirectPortPair = selectedItem.data(_qtc.Qt.UserRole)

            self._removePorts(selectedDirectPortPair.fromPort, selectedDirectPortPair.toPort)

            self.storage.directPortPairs.remove(selectedDirectPortPair)

            row = directPortPairsListWidget.row(selectedItem)
            directPortPairsListWidget.takeItem(row)

    def removeHxL(self):
        self._removeSelectedHeatExchangers(self.leftHeatExchangersItemListWidget)

    def removeHxR(self):
        self._removeSelectedHeatExchangers(self.rightHeatExchangersItemListWidget)

    def _removeSelectedHeatExchangers(self, heatExchangersItemListWidget):
        for selectedItem in heatExchangersItemListWidget.selectedItems():
            heatExchanger: _st.HeatExchanger = selectedItem.data(_qtc.Qt.UserRole)

            self._removePorts(heatExchanger.port1, heatExchanger.port2)

            self.storage.heatExchangers.remove(heatExchanger)
            self.storage.editor.diagramScene.removeItem(heatExchanger)

            row = heatExchangersItemListWidget.row(selectedItem)
            heatExchangersItemListWidget.takeItem(row)

    def _removePorts(self, fromPort, toPort):
        self._removeConnectionIfAny(fromPort)
        self._removeConnectionIfAny(toPort)
        self.storage.inputs.remove(fromPort)
        self.storage.outputs.remove(toPort)
        self.storage.editor.diagramScene.removeItem(fromPort)
        self.storage.editor.diagramScene.removeItem(toPort)

    def _removeConnectionIfAny(self, port):
        if port.isConnected():
            connection = port.getConnection()
            _hls.split(connection, self._editor.hydraulicLoops, self._editor.fluids)
            connection.deleteConnection()

    def modifyHx(self):
        result = self._getFirstSelectedItemAndHeatExchanger()
        if not result:
            return
        selectedItem, heatExchanger = result

        modifyDialog = _mhd.ModifyRelativeHeightsDialog(
            heatExchanger.relativeInputHeight, heatExchanger.relativeOutputHeight
        )
        newHeights = modifyDialog.newRelativeHeights
        if not newHeights:
            return

        newInputHeight = newHeights.input if newHeights.input != "empty" else heatExchanger.relativeInputHeight
        newOutputHeight = newHeights.output if newHeights.output != "empty" else heatExchanger.relativeOutputHeight
        heatExchanger.setRelativeHeights(newInputHeight, newOutputHeight)

        listText = self._getHeatExchangerListItemText(heatExchanger)
        selectedItem.setText(listText)

    def _getFirstSelectedItemAndHeatExchanger(self):
        leftSelectedItems = self.leftHeatExchangersItemListWidget.selectedItems()
        rightSelectedItems = self.rightHeatExchangersItemListWidget.selectedItems()

        if leftSelectedItems:
            side = 0
            selectedItem = leftSelectedItems[0]
        elif rightSelectedItems:
            side = 2
            selectedItem = rightSelectedItems[0]
        else:
            return None

        name = selectedItem.text().split(",")[0]
        for heatExchanger in self.storage.heatExchangers:
            if heatExchanger.displayName == name and heatExchanger.sSide == side:
                return selectedItem, heatExchanger

        raise AssertionError(f"No heat exchanger with name {name} found.")

    def modifyPort(self):
        selectedItem = self._getFirstSelectedDirectPortPairListWidgetItem()
        if not selectedItem:
            return

        directPortPair: _dpp.DirectPortPair = selectedItem.data(_qtc.Qt.UserRole)

        dialogResult = _mhd.ModifyRelativeHeightsDialog(
            directPortPair.relativeInputHeight, directPortPair.relativeOutputHeight
        )
        newHeights = dialogResult.newRelativeHeights
        if not newHeights:
            return

        newRelativeInputHeight = newHeights.input if newHeights.input != "empty" else directPortPair.relativeInputHeight
        newRelativeOutputHeight = (
            newHeights.output if newHeights.output != "empty" else directPortPair.relativeOutputHeight
        )

        directPortPair.setRelativeHeights(newRelativeInputHeight, newRelativeOutputHeight, self.storage.h)

        newText = self._getDirectPortPairListItemText(directPortPair)
        selectedItem.setText(newText)

    def _getFirstSelectedDirectPortPairListWidgetItem(
        self,
    ) -> _tp.Optional[QListWidgetItem]:
        leftSelectedItems = self.leftDirectPortPairsItemListWidget.selectedItems()
        if leftSelectedItems:
            return leftSelectedItems[0]

        rightSelectedItems = self.rightDirectPortPairsItemListWidget.selectedItems()
        if rightSelectedItems:
            return rightSelectedItems[0]

        return None

    def increaseSize(self):
        self._changeSize(self.HEIGHT_INCREMENT, self.WIDTH_INCREMENT)

    def decreaseSize(self):
        self._changeSize(-self.HEIGHT_INCREMENT, -self.WIDTH_INCREMENT)

    def _changeSize(self, deltaH: int, deltaW: int) -> None:
        newWidth = self.storage.w + deltaW
        newHeight = self.storage.h + deltaH
        self.storage.setSize(width=newWidth, height=newHeight)
        self.storage.updateImage()

    def cancel(self):
        self.close()

    def _openMessageBox(self, text):
        self.msgb.setText(text)
        if not self.isTest:
            self.msgb.exec_()
