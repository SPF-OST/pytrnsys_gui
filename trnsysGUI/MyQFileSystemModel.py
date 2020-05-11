from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileSystemModel


class MyQFileSystemModel(QFileSystemModel):
    """
    Self defined QFileSystemModel in order to override headerData method
    """

    def setName(self, name):
        self.name = name

    def headerData(self, section, orientation, role):
        """
        To change the column name to correspond to object names
        """
        if section == 0 and role == Qt.DisplayRole:
            return self.name
        else:
            return super(QFileSystemModel, self).headerData(section, orientation, role)
