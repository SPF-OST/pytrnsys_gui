from PyQt5.QtCore import Qt, QModelIndex
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
        if section == 4 and role == Qt.DisplayRole:
            return 'Priority'
        else:
            return super(QFileSystemModel, self).headerData(section, orientation, role)

    def columnCount(self, parent=QModelIndex()):
        return super(MyQFileSystemModel, self).columnCount() + 1

    def data(self, index, role):
        if index.column() == self.columnCount() - 1:
            if role == Qt.DisplayRole:
                return "0"
            if role == Qt.TextAlignmentRole:
                return Qt.AlignHCenter
        return super(MyQFileSystemModel, self).data(index, role)

    def setData(self, index, value, role):
        print("This is ran0")
        print(self.columnCount() - 1, index.column(), value)
        if index.column() == 4:
            print("This is ran1")
            if role == Qt.DisplayRole:
                print("This is ran2")
                return value
        return super(MyQFileSystemModel, self).setData(index, value, role)
    # def setData(self, index, value, role):
    #     if index.column() == 0:
    #         if role == Qt.DisplayRole:
    #             return value
    #         if role == Qt.TextAlignmentRole:
    #             return Qt.AlignHCenter
    #     return super(MyQFileSystemModel, self).setData(index, value, role)