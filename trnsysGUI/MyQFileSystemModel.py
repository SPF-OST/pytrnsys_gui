from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileSystemModel


class MyQFileSystemModel(QFileSystemModel):

    def setName(self, name):
        self.name = name

    def headerData(self, section, orientation, role):
        if section == 0 and role == Qt.DisplayRole:
            return self.name
        else:
            return super(QFileSystemModel, self).headerData(section, orientation, role)
