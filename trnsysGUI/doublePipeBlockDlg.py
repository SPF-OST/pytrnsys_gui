# pylint: skip-file
# type: ignore

from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QPushButton

import trnsysGUI.BlockItem as _bi
import trnsysGUI.names.dialog as _ndialog
import trnsysGUI.names.rename as _rename


class DoublePipeBlockDlg(_ndialog.ChangeNameDialogBase):
    def __init__(self, blockItem: _bi.BlockItem, renameHelper: _rename.RenameHelper) -> None:
        super().__init__(blockItem, renameHelper)

        self._blockItem = blockItem
        self.okButton = QPushButton("OK")
        self.cancelButton = QPushButton("Cancel")

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.okButton)
        buttonLayout.addWidget(self.cancelButton)
        layout = QGridLayout()
        nameLabel = QLabel("Name:")
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
