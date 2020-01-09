from pathlib import Path

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PyQt5.QtWidgets import QMenu, QFileDialog

from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.PortItem import PortItem
from trnsysGUI.newPortDlg import newPortDlg


class GenericBlock(BlockItem):
    def __init__(self, trnsysType, parent, **kwargs):
        super(GenericBlock, self).__init__(trnsysType, parent, **kwargs)

        self.inputs.append(PortItem('i', 2, self))
        self.outputs.append(PortItem('o', 2, self))

        self.pixmap = QPixmap(self.image)
        self.setPixmap(self.pixmap.scaled(QSize(self.w, self.h)))

        self.imagesource = ("images/" + self.name)
        self.changeSize()

    def changeSize(self):
        # print("passing through c change size")
        w = self.w
        h = self.h

        """ Resize block function """
        delta = 4
        deltaH = self.h / 10

        # Limit the block size:
        if h < 20:
            h = 20
        if w < 40:
            w = 40
        # center label:
        rect = self.label.boundingRect()
        lw, lh = rect.width(), rect.height()
        lx = (w - lw) / 2
        self.label.setPos(lx, h)

        # Update port positions:
        self.outputs[0].setPos(2 * delta - 4 * self.flippedH * delta - self.flippedH * w + w,
                               h - h * self.flippedV - deltaH + 2 * deltaH * self.flippedV)
        self.inputs[0].setPos(2 * delta - 4 * self.flippedH * delta - self.flippedH * w + w,
                              h * self.flippedV + deltaH - 2 * deltaH * self.flippedV)
        self.inputs[0].side = 2 - 2 * self.flippedH
        self.outputs[0].side = 2 - 2 * self.flippedH

        return w, h

    def addPortDlg(self):
        newPortDlg(self, self.parent.parent())

    def addPort(self, io, relH):
        print(io)
        print(relH)

    def setImage(self, name):
        print("Setting image with name" + name)
        self.image = QImage(name)
        self.pixmap = QPixmap(self.image)
        self.setPixmap(self.pixmap.scaled(QSize(self.w, self.h)))

    def changeImage(self):
        name = str(self.pickImage().resolve())
        if name != "":
            self.setImage(name)
            self.setImagesource(name)

    def setImagesource(self, name):
        self.imagesource = name

    def pickImage(self):
        return Path(QFileDialog.getOpenFileName(self.parent.parent(), filter="*.png")[0])

    def contextMenuEvent(self, event):
        menu = QMenu()

        lNtp = QIcon('images/Notebook.png')
        a1 = menu.addAction(lNtp, 'Launch NotePad++')
        a1.triggered.connect(self.launchNotepadFile)

        rr = QIcon('images/rotate-to-right.png')
        a2 = menu.addAction(rr, 'Rotate Block clockwise')
        a2.triggered.connect(self.rotateBlockCW)

        ll = QIcon('images/rotate-left.png')
        a3 = menu.addAction(ll, 'Rotate Block counter-clockwise')
        a3.triggered.connect(self.rotateBlockCCW)

        rRot = QIcon('images/move-left.png')
        a4 = menu.addAction(rRot, 'Reset Rotation')
        a4.triggered.connect(self.resetRotation)

        b1 = menu.addAction('Print Rotation')
        b1.triggered.connect(self.printRotation)

        dB = QIcon('images/close.png')
        c1 = menu.addAction(dB, 'Delete this Block')
        c1.triggered.connect(self.deleteBlock)

        # sG = QIcon('')
        c2 = menu.addAction("Set group")
        c2.triggered.connect(self.configGroup)

        c3 = menu.addAction("Set image")
        c3.triggered.connect(self.changeImage)

        c4 = menu.addAction("Add port")
        c4.triggered.connect(self.addPortDlg)

        d1 = menu.addAction('Dump information')
        d1.triggered.connect(self.dumpBlockInfo)

        e1 = menu.addAction('Inspect')
        e1.triggered.connect(self.inspectBlock)

        menu.exec_(event.screenPos())
