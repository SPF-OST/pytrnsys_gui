from __future__ import annotations

import dataclasses as _dc
import typing as _tp


if _tp.TYPE_CHECKING:
    import trnsysGUI.connection.connectionBase as _cb
    from trnsysGUI import cornerItem as _ci


@_dc.dataclass
class Node:
    parent: _tp.Optional[_tp.Union[_cb.ConnectionBase, _ci.CornerItem]] = None
    prevNode: _tp.Optional[Node] = None
    nextNode: _tp.Optional[Node] = None

    def nextN(self) -> _tp.Optional[Node]:
        return self.nextNode

    def prevN(self) -> _tp.Optional[Node]:
        return self.prevNode

    def setPrev(self, prevNode) -> None:
        self.prevNode = prevNode

    def setNext(self, nextNode) -> None:
        self.nextNode = nextNode

    def setParent(self, parent) -> None:
        self.parent = parent

    def firstNode(self) -> Node:
        res = self
        while res.prevNode is not None:
            res = res.prevNode

        return res

    def lastNode(self) -> Node:
        res = self

        nextNode = res.nextN()
        while nextNode:
            res = nextNode
            nextNode = res.nextN()

        return res
