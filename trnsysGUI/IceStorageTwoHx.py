from trnsysGUI.BlockItemFourPorts import BlockItemFourPorts

class IceStorageTwoHx(BlockItemFourPorts):
    def __init__(self, trnsysType, parent, **kwargs):
        super(IceStorageTwoHx, self).__init__(trnsysType, parent, **kwargs)
        self.changeSize()

    def changeSize(self):
        w = self.w
        h = self.h

        """ Resize block function """
        delta = 20

        # center label:
        rect = self.label.boundingRect()
        lw, lh = rect.width(), rect.height()
        lx = (w - lw) / 2
        self.label.setPos(lx, h)

        self.inputs[0].setPos(0,delta)
        self.inputs[1].setPos(w,delta)
        self.inputs[0].side = (self.rotationN +2 * self.flippedH) % 4
        self.inputs[1].side = (self.rotationN + 2 - 2 * self.flippedH) % 4

        self.outputs[0].setPos(0,h-delta)
        self.outputs[1].setPos(w,h-delta)
        self.outputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.outputs[1].side = (self.rotationN + 2 - 2 * self.flippedH) % 4

        return w, h