# pylint: skip-file
# type: ignore

from PyQt5.QtCore import QMimeData, Qt
from PyQt5.QtGui import QStandardItemModel


class LibraryModel(QStandardItemModel):
    def __init__(self, parent=None):
        QStandardItemModel.__init__(self, parent)

    def mimeTypes(self):
        return ["component/name"]

    def mimeData(self, idxs):
        mimedata = QMimeData()
        for idx in idxs:
            if idx.isValid():
                txt = self.data(idx, Qt.DisplayRole)
                txt2 = bytearray()
                txt2.extend(map(ord, txt))
                mimedata.setData("component/name", txt2)
        return mimedata
