# pylint: skip-file
# type: ignore

import typing as _tp

from PyQt5.QtWidgets import (
    QLabel,
    QLineEdit,
    QGridLayout,
    QHBoxLayout,
    QListWidget,
    QPushButton,
    QSpacerItem,
    QVBoxLayout,
    QRadioButton,
    QDialog,
    QTabWidget,
    QWidget,
    QMessageBox,
    QListWidgetItem,
)
import PyQt5.QtCore as _qtc

import trnsysGUI.directPortPair as _dpp
import trnsysGUI.side as _side
from trnsysGUI.modifyRelativeHeightsDialog import ModifyRelativeHeightsDialog


class ConfigureStorageDialog(QDialog):
    WIDTH_INCREMENT = 10
    HEIGHT_INCREMENT = 100

    def __init__(self, storage, parent):
        super(ConfigureStorageDialog, self).__init__(parent)
        self.parent = parent
        self.storage = storage
        self.n = 0
        self.m = 0

        spacerHeight = 15

        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()

        self.tabs.addTab(self.tab1, "Heat exchangers")
        self.tabs.addTab(self.tab2, "Direct ports")

        h0 = QHBoxLayout()
        description = QLabel("Please configure the storage tank:")
        exportButton = QPushButton("Export ddck")
        exportButton.clicked.connect(self.storage.exportDck)

        h0.addWidget(description)
        h0.addWidget(exportButton)

        tankNameLabel = QLabel()
        tankNameLabel.setText("<b>Tank name: </b>")
        self.le = QLineEdit(self.storage.label.toPlainText())

        gl = QGridLayout()
        hxsLabel = QLabel("<b>Heat Exchangers </b>")
        gl.addWidget(hxsLabel, 0, 0, 1, 2)

        qhbL = QHBoxLayout()

        self.leftHeatExchangersItemListWidget = QListWidget()
        qhbL.addWidget(self.leftHeatExchangersItemListWidget)

        self.rightHeatExchangersItemListWidget = QListWidget()
        qhbL.addWidget(self.rightHeatExchangersItemListWidget)

        offsetLabel = QLabel("Height offsets in percent")
        offsetLeILabel = QLabel("Input (upper port): ")
        offsetLeOLabel = QLabel("Output (lower port):")
        self.offsetLeI = QLineEdit("0")
        self.offsetLeO = QLineEdit("0")
        self.lButton = QRadioButton("Left side")
        self.rButton = QRadioButton("Right side")

        gl.addWidget(offsetLabel, 3, 0, 1, 1)
        gl.addWidget(offsetLeILabel, 4, 0, 1, 1)
        gl.addWidget(self.offsetLeI, 5, 0, 1, 3)
        gl.addWidget(offsetLeOLabel, 6, 0, 1, 1)
        gl.addWidget(self.offsetLeO, 7, 0, 1, 3)

        self.hxNameLe = QLineEdit()
        self.hxNameLe.setPlaceholderText("Enter a name...")
        gl.addWidget(self.hxNameLe, 8, 0, 1, 3)

        gl.addWidget(self.lButton, 9, 0, 1, 1)
        gl.addWidget(self.rButton, 9, 2, 1, 1)

        addButton = QPushButton("Add...")
        addButton.clicked.connect(self.addHx)
        gl.addWidget(addButton, 10, 0, 1, 1)
        removeButton = QPushButton("Remove...")
        removeButton.clicked.connect(self.removeHxL)
        removeButton.clicked.connect(self.removeHxR)
        gl.addWidget(removeButton, 10, 1, 1, 1)
        modifyButton = QPushButton("Modify")
        modifyButton.clicked.connect(self.modifyHx)
        gl.addWidget(modifyButton, 10, 2, 1, 1)
        spaceHx = QSpacerItem(self.width(), spacerHeight)
        gl.addItem(spaceHx, 11, 0, 1, 2)

        manPortLay = QVBoxLayout()
        qhbL2 = QHBoxLayout()

        self._leftDirectPortPairsItemListWidget = QListWidget()
        qhbL2.addWidget(self._leftDirectPortPairsItemListWidget)

        self._rightDirectPortPairsItemListWidget = QListWidget()
        qhbL2.addWidget(self._rightDirectPortPairsItemListWidget)

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
        self.manAddButton.clicked.connect(self.manAddPortPair)

        self.manRemovebutton = QPushButton("Remove ports")
        self.manRemovebutton.clicked.connect(self.manRemovePortPairLeft)
        self.manRemovebutton.clicked.connect(self.manRemovePortPairRight)

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

        increaseSizeButton.clicked.connect(self.incrSize)
        decreaseSizeButton.clicked.connect(self.decrSize)
        self.okButton.clicked.connect(self.acceptedEdit)
        self.cancelButton.clicked.connect(self.cancel)

        L = QVBoxLayout()
        L.addLayout(h0)
        L.addWidget(tankNameLabel)
        L.addWidget(self.le)

        t1Layout = QVBoxLayout()
        t1Layout.addLayout(qhbL)
        t1Layout.addLayout(gl)

        self.tab1.setLayout(t1Layout)

        self.tab2.setLayout(manPortLay)

        L.addWidget(self.tabs)

        L.addWidget(increaseSizeButton)
        L.addWidget(decreaseSizeButton)
        L.addWidget(self.okButton)
        L.addWidget(self.cancelButton)

        self.setLayout(L)

        self._loadHeatExchangers()
        self._loadDirectPortPairs()

        # This is to ensure that only one list element is selected
        self.rightHeatExchangersItemListWidget.setSelectionMode(1)
        self.leftHeatExchangersItemListWidget.setSelectionMode(1)
        self.rightHeatExchangersItemListWidget.clicked.connect(self.listWRClicked)
        self.leftHeatExchangersItemListWidget.clicked.connect(self.listWLClicked)

        self._rightDirectPortPairsItemListWidget.setSelectionMode(1)
        self._leftDirectPortPairsItemListWidget.setSelectionMode(1)
        self._rightDirectPortPairsItemListWidget.clicked.connect(self.listWR2Clicked)
        self._leftDirectPortPairsItemListWidget.clicked.connect(self.listWL2Clicked)

        self.show()

    def _loadHeatExchangers(self):
        for h in self.storage.heatExchangers:
            listItem = self._getHeatExchangerListItemText(h)
            if h.sSide == 0:
                self.leftHeatExchangersItemListWidget.addItem(listItem)
            if h.sSide == 2:
                self.rightHeatExchangersItemListWidget.addItem(listItem)

    @staticmethod
    def _getHeatExchangerListItemText(h):
        return (
            h.displayName
            + ", y_offset = "
            + "%d" % int(h.relativeInputHeight * 100)
            + "%"
            + " to "
            + "%d" % int(h.relativeOutputHeight * 100)
            + "%"
        )

    def _loadDirectPortPairs(self):
        directPortPair: _dpp.DirectPortPair
        for directPortPair in self.storage.directPortPairs:
            itemText = self._getDirectPortPairListItemText(directPortPair)
            item = QListWidgetItem(itemText)
            item.setData(_qtc.Qt.UserRole, directPortPair)

            if directPortPair.isOnLeftSide:
                self._leftDirectPortPairsItemListWidget.addItem(item)
            else:
                self._rightDirectPortPairsItemListWidget.addItem(item)

    @staticmethod
    def _getDirectPortPairListItemText(directPortPair: _dpp.DirectPortPair):
        return (
            "Port pair from "
            + "%d%%" % int(directPortPair.relativeInputHeight * 100)
            + " to "
            + "%d%%" % int(directPortPair.relativeOutputHeight * 100)
        )

    def listWLClicked(self):
        self.rightHeatExchangersItemListWidget.clearSelection()

    def listWRClicked(self):
        self.leftHeatExchangersItemListWidget.clearSelection()

    def listWL2Clicked(self):
        self._rightDirectPortPairsItemListWidget.clearSelection()

    def listWR2Clicked(self):
        self._leftDirectPortPairsItemListWidget.clearSelection()

    def addHx(self):
        """
        Checks whether the inputs are in the correct range [0,100] and in order, and calls the function for creating a
        HeatExchanger on the respective side.

        Returns
        -------
        """
        if (
            self.minOffsetDistance()
            and float(self.offsetLeI.text()) > float(self.offsetLeO.text())
            and self.offsetsInRange()
        ):
            print("Adding hx")
            if self.rButton.isChecked():
                print("addhxr")
                self.addHxR()
            if self.lButton.isChecked():
                print("addhxl")
                self.addHxL()
        else:
            msgb = QMessageBox()
            msgb.setText(
                "At least 20% of difference and larger top port than bottom port needed and valid range [0, 100]"
            )
            msgb.exec_()

    def minOffsetDistance(self):
        return abs(float(self.offsetLeI.text()) - float(self.offsetLeO.text())) >= 5

    def offsetsInRange(self):
        return (0 <= float(self.offsetLeI.text()) <= 100) and (
            0 <= float(self.offsetLeO.text()) <= 100
        )

    def addHxL(self):
        self._addHeatExchanger(_side.Side.LEFT)

    def addHxR(self):
        self._addHeatExchanger(_side.Side.RIGHT)

    def _addHeatExchanger(self, side: _side.Side):
        name = self.hxNameLe.text()
        if not name:
            messageBox = QMessageBox()
            messageBox.setText(
                "Please specify the name of the heat exchanger that you want to add."
            )
            messageBox.exec_()
            return

        relativeInputHeight = float(self.offsetLeI.text()) / 100
        relativeOutputHeight = float(self.offsetLeO.text()) / 100

        heatExchanger = self.storage.addHeatExchanger(name, side, relativeInputHeight, relativeOutputHeight)

        itemText = self._getHeatExchangerListItemText(heatExchanger)
        if side == _side.Side.LEFT:
            self.leftHeatExchangersItemListWidget.addItem(itemText)
        else:
            self.rightHeatExchangersItemListWidget.addItem(itemText)

    def manAddPortPair(self):
        if float(self.manPortLeI.text()) > 100:
            self.manPortLeI.setText("100")

        if float(self.manPortLeO.text()) < 0:
            self.manPortLeO.setText("0")

        self.storage.addDirectPortPair(
            self.manlButton.isChecked(),
            float(self.manPortLeI.text()) / 100,
            float(self.manPortLeO.text()) / 100,
            self.storage.h,
        )

        self._leftDirectPortPairsItemListWidget.clear()
        self._rightDirectPortPairsItemListWidget.clear()
        self._loadDirectPortPairs()

    def manRemovePortPairLeft(self):
        self._removeSelectedPortPairs(self._leftDirectPortPairsItemListWidget)

    def manRemovePortPairRight(self):
        self._removeSelectedPortPairs(self._rightDirectPortPairsItemListWidget)

    def _removeSelectedPortPairs(self, directPortPairsListWidget):
        for selectedItem in directPortPairsListWidget.selectedItems():
            selectedDirectPortPair = selectedItem.data(_qtc.Qt.UserRole)

            self.storage.directPortPairs.remove(selectedDirectPortPair)

            row = directPortPairsListWidget.row(selectedItem)
            directPortPairsListWidget.takeItem(row)

            while len(selectedDirectPortPair.fromPort.connectionList) > 0:
                selectedDirectPortPair.fromPort.connectionList[0].deleteConn()

            while len(selectedDirectPortPair.toPort.connectionList) > 0:
                selectedDirectPortPair.toPort.connectionList[0].deleteConn()

            self.storage.inputs.remove(selectedDirectPortPair.fromPort)
            self.storage.outputs.remove(selectedDirectPortPair.toPort)

            self.storage.parent.scene().removeItem(selectedDirectPortPair.fromPort)
            self.storage.parent.scene().removeItem(selectedDirectPortPair.toPort)

    def removeHxL(self):
        self._removeSelectedHeatExchangers(self.leftHeatExchangersItemListWidget)

    def removeHxR(self):
        self._removeSelectedHeatExchangers(self.rightHeatExchangersItemListWidget)

    def _removeSelectedHeatExchangers(self, heatExchangersItemListWidget):
        for selectedItem in heatExchangersItemListWidget.selectedItems():
            heatExchanger = selectedItem.data(_qtc.Qt.UserRole)

            self.storage.heatExchangers.remove(heatExchanger)

            row = heatExchangersItemListWidget.row(selectedItem)
            heatExchangersItemListWidget.takeItem(row)

            while len(heatExchanger.port1.connectionList) > 0:
                heatExchanger.port1.connectionList[0].deleteConn()

            while len(heatExchanger.port2.connectionList) > 0:
                heatExchanger.port2.connectionList[0].deleteConn()

            self.storage.inputs.remove(heatExchanger.port1)
            self.storage.outputs.remove(heatExchanger.port2)

            self.storage.parent.scene().removeItem(heatExchanger.port1)
            self.storage.parent.scene().removeItem(heatExchanger.port2)
            self.storage.parent.scene().removeItem(heatExchanger)

    def modifyHx(self):
        """
        Modify Hx.
        """
        result = self._getFirstSelectedItemAndHeatExchanger()
        if not result:
            return
        selectedItem, heatExchanger = result

        modifyDialog = ModifyRelativeHeightsDialog(
            heatExchanger.relativeInputHeight, heatExchanger.relativeOutputHeight
        )
        newHeights = modifyDialog.newRelativeHeights
        if not newHeights:
            return

        newInputHeight = (
            newHeights.input
            if newHeights.input != "empty"
            else heatExchanger.relativeInputHeight
        )
        newOutputHeight = (
            newHeights.output
            if newHeights.output != "empty"
            else heatExchanger.relativeOutputHeight
        )
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
        """
        Modify existing ports.
        """
        selectedItem = self._getFirstSelectedDirectPortPairListWidgetItem()
        if not selectedItem:
            return

        directPortPair: _dpp.DirectPortPair = selectedItem.data(_qtc.Qt.UserRole)

        dialogResult = ModifyRelativeHeightsDialog(
            directPortPair.relativeInputHeight, directPortPair.relativeOutputHeight
        )
        newHeights = dialogResult.newRelativeHeights
        if not newHeights:
            return

        newRelativeInputHeight = (
            newHeights.input
            if newHeights.input != "empty"
            else directPortPair.relativeInputHeight
        )
        newRelativeOutputHeight = (
            newHeights.output
            if newHeights.output != "empty"
            else directPortPair.relativeOutputHeight
        )

        directPortPair.setRelativeHeights(
            newRelativeInputHeight, newRelativeOutputHeight, self.storage.h
        )

        newText = self._getDirectPortPairListItemText(directPortPair)
        selectedItem.setText(newText)

    def _getFirstSelectedDirectPortPairListWidgetItem(
        self,
    ) -> _tp.Optional[QListWidgetItem]:
        leftSelectedItems = self._leftDirectPortPairsItemListWidget.selectedItems()
        if leftSelectedItems:
            return leftSelectedItems[0]

        rightSelectedItems = self._rightDirectPortPairsItemListWidget.selectedItems()
        if rightSelectedItems:
            return rightSelectedItems[0]

        return None

    def incrSize(self):
        self._changeSize(self.HEIGHT_INCREMENT, self.WIDTH_INCREMENT)

    def decrSize(self):
        self._changeSize(-self.HEIGHT_INCREMENT, -self.WIDTH_INCREMENT)

    def _changeSize(self, deltaH, deltaW):
        self.storage.updatePortItemPositions(deltaH, deltaW)
        self.storage.h += deltaH
        self.storage.w += deltaW
        self.storage.updateHeatExchangersAfterTankSizeChange()
        self.storage.updateImage()

    def acceptedEdit(self):
        # print("Changing displayName")
        test = self.le.text()
        if self.le.text() == "":
            qmb = QMessageBox()
            qmb.setText("Please set a name for this storage tank.")
            qmb.setStandardButtons(QMessageBox.Ok)
            qmb.setDefaultButton(QMessageBox.Ok)
            qmb.exec()
            return
        self.storage.setName(self.le.text())
        self.close()

    def cancel(self):
        self.close()
