class Node(object):
    def __init__(self, parent=None, prevNode=None, nextNode=None):
        self.prevNode = prevNode
        self.nextNode = nextNode
        self.parent = parent

    # Still deciding if direct access to attributes is ok
    def nextN(self):
        return self.nextNode

    def prevN(self):
        return self.prevNode

    def setPrev(self, prevNode):
        self.prevNode = prevNode

    def setNext(self, nextNode):
        self.nextNode = nextNode

    def setParent(self, parent):
        self.parent = parent

    def firstNode(self):
        # Recursion
        # if self.prevNode is not None:
        #     return self.prevNode.beginNode()
        # else:
        #     return self

        # Should do the same:
        res = self
        while res.prevNode is not None:
            res = res.prevNode

        return res

    def lastNode(self):
        # Recursion
        # if self.nextNode is not None:
        #     return self.nextnode.lastNode()
        # else:
        #     return self

        # Should do the same:
        res = self
        while res.nextN() is not None:
            res = res.nextN()
            # print("In traversal... at node " + str(self) + " has parent " + str(self.parent))
        return res

    def countNodes(self):
        res = 1
        n = self.firstNode(self)
        while res.nextN() is not None:
            res += 1
            n = n.nextN()
        print("This connection has " + str(res) + "nodes")
        return res
