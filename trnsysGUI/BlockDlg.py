# pylint: disable=invalid-name

import PyQt5.QtGui as _qtg
import PyQt5.QtWidgets as _qtw

import trnsysGUI.BlockItem as _bi
import trnsysGUI.names.dialog as _ndialog
import trnsysGUI.names.rename as _rename


class BlockDlg(_ndialog.ChangeNameDialogBase):  # pylint: disable=too-many-instance-attributes
    def __init__(self, blockItem: _bi.BlockItem, renameHelper: _rename.RenameHelper) -> None:
        super().__init__(blockItem, renameHelper)
        self._blockItem = blockItem
        self._renameHelper = renameHelper

        self.setWindowIcon(_qtg.QIcon(blockItem.pixmap()))
        self.okButton = _qtw.QPushButton("OK")
        self.cancelButton = _qtw.QPushButton("Cancel")

        self.hFlipBoxLabel = _qtw.QLabel("Horizontal Flip")
        self.vFlipBoxLabel = _qtw.QLabel("Vertical Flip")

        self.hFlipBox = _qtw.QCheckBox()
        self.vFlipBox = _qtw.QCheckBox()

        self.vFlipBox.setTristate(False)
        self.hFlipBox.setTristate(False)
        self.hFlipBox.setCheckState(self._blockItem.flippedH * 2)  # type: ignore[arg-type]
        self.vFlipBox.setCheckState(self._blockItem.flippedV * 2)  # type: ignore[arg-type]

        flipLayout = _qtw.QHBoxLayout()
        flipLayout.addWidget(self.hFlipBoxLabel)
        flipLayout.addWidget(self.hFlipBox)
        flipLayout.addWidget(self.vFlipBoxLabel)
        flipLayout.addWidget(self.vFlipBox)

        buttonLayout = _qtw.QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.okButton)
        buttonLayout.addWidget(self.cancelButton)
        layout = _qtw.QGridLayout()
        nameLabel = _qtw.QLabel("Name:")
        layout.addWidget(nameLabel, 0, 0)
        layout.addWidget(self._displayNameLineEdit, 0, 1)
        layout.addLayout(flipLayout, 1, 0, 2, 0)
        layout.addLayout(buttonLayout, 2, 0, 2, 0)
        self.setLayout(layout)

        self.setFixedSize(300, 150)

        self.okButton.clicked.connect(self.acceptedEdit)
        self.cancelButton.clicked.connect(self.cancel)
        self.hFlipBox.stateChanged.connect(self.setNewFlipStateH)
        self.vFlipBox.stateChanged.connect(self.setNewFlipStateV)
        self.setWindowTitle("Properties")
        self.show()

    def setNewFlipStateH(self, state):
        self._blockItem.updateFlipStateH(state)
        self._blockItem.updateSidesFlippedH()

    def setNewFlipStateV(self, state):
        self._blockItem.updateFlipStateV(state)
        self._blockItem.updateSidesFlippedV()

    def cancel(self):
        self.close()
