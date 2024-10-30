import pathlib as _pl

import PyQt5.QtWidgets as _qtw

import trnsysGUI.BlockItem as _bi
import trnsysGUI.names.dialog as _ndialog
import trnsysGUI.names.rename as _rename


class DoublePipeBlockDlg(_ndialog.ChangeNameDialogBase):
    def __init__(
        self,
        blockItem: _bi.BlockItem,
        renameHelper: _rename.RenameHelper,
        projectFolder: str,
    ) -> None:
        super().__init__(blockItem, renameHelper, _pl.Path(projectFolder))

        self._blockItem = blockItem
        self.okButton = _qtw.QPushButton("OK")
        self.cancelButton = _qtw.QPushButton("Cancel")

        buttonLayout = _qtw.QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.okButton)
        buttonLayout.addWidget(self.cancelButton)
        layout = _qtw.QGridLayout()
        nameLabel = _qtw.QLabel("Name:")
        layout.addWidget(nameLabel, 0, 0)
        layout.addWidget(self._displayNameLineEdit, 0, 1)
        layout.addLayout(buttonLayout, 2, 0, 2, 0)
        self.setLayout(layout)

        self.setFixedSize(300, 150)

        self.okButton.clicked.connect(self.acceptedEdit)
        self.cancelButton.clicked.connect(self.cancel)
        self.setWindowTitle("Properties")
        self.show()

    def cancel(self):
        self.close()
