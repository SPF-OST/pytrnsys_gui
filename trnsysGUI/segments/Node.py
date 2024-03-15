# pylint: skip-file
# type: ignore


class Node:
    def __init__(self, parent=None, prevNode=None, nextNode=None):
        """
        Nodes
        can
        have as parent
        1)Connection (then it is at a PortItem)
        2)CornerItem

        Parameters
        ----------
        parent
        prevNode
        nextNode
        """

        self.prevNode = prevNode
        self.nextNode = nextNode
        self.parent = parent

    def nextN(self) -> "Node":
        return self.nextNode

    def prevN(self) -> "Node":
        return self.prevNode

    def setPrev(self, prevNode):
        self.prevNode = prevNode

    def setNext(self, nextNode):
        self.nextNode = nextNode

    def setParent(self, parent):
        self.parent = parent

    def firstNode(self):
        res = self
        while res.prevNode is not None:
            res = res.prevNode

        return res

    def lastNode(self):
        res = self
        while res.nextN() is not None:
            res = res.nextN()
        return res
