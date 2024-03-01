# pylint: disable = too-many-lines

from __future__ import annotations

import math as _math
import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtWidgets as _qtw

import trnsysGUI.CornerItem as _ci
import trnsysGUI.PortItemBase as _pib
import trnsysGUI.connection.delete as _cdel
import trnsysGUI.connection.values as _values
import trnsysGUI.idGenerator as _id
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.segments.Node as _node
import trnsysGUI.segments.SegmentItemBase as _sib

if _tp.TYPE_CHECKING:
    import trnsysGUI.diagram.Editor as _ed


def calcDist(p1, p2):  # pylint: disable = invalid-name
    vec = p1 - p2
    norm = _math.sqrt(vec.x() ** 2 + vec.y() ** 2)
    return norm


class ConnectionBase(_qtw.QGraphicsItem, _ip.HasInternalPiping):
    # pylint: disable = too-many-public-methods, too-many-instance-attributes
    def __init__(
        self,
        displayName: str,
        fromPort: _pib.PortItemBase,
        toPort: _pib.PortItemBase,
        shallBeSimulated: bool,
        lengthInMeters: _values.Value,
        parent: _ed.Editor,  # type: ignore[name-defined]
    ) -> None:
        super().__init__(parent=None)

        assert isinstance(fromPort.parent, _ip.HasInternalPiping) and isinstance(toPort.parent, _ip.HasInternalPiping)

        self.logger = parent.logger

        self._fromPort = fromPort
        self._toPort = toPort

        self.shallBeSimulated = shallBeSimulated
        self.lengthInM = lengthInMeters

        self.displayName = displayName

        self.parent = parent
        self._editor = parent

        # Global
        self.id = self.parent.idGen.getID()  # pylint: disable = invalid-name
        self.connId = self.parent.idGen.getConnID()
        self.trnsysId = self.parent.idGen.getTrnsysID()

        self.segments: _tp.List[_sib.SegmentItemBase] = []  # type: ignore[name-defined]

        self.isConnectionSelected = False

        self.startNode = _node.Node(self)  # type: ignore[attr-defined]
        self.endNode = _node.Node(self)  # type: ignore[attr-defined]
        self.firstS: _tp.Optional[_sib.SegmentItemBase] = None  # type: ignore[name-defined]

        self.startPos = None

        self.initNew(parent)

    def boundingRect(self) -> _qtc.QRectF:
        return self.childrenBoundingRect()

    def paint(
        self, painter: _qtg.QPainter, option: _qtw.QStyleOptionGraphicsItem, widget: _tp.Optional[_qtw.QWidget] = None
    ) -> None:
        for child in self.childItems():
            child.paint(painter, option, widget)

    def getDisplayName(self) -> str:
        return self.displayName

    def hasDdckPlaceHolders(self) -> bool:
        return False

    def shallRenameOutputTemperaturesInHydraulicFile(self):
        return False

    def getModelPipe(self, portItemType: _mfn.PortItemType) -> _mfn.Pipe:
        raise NotImplementedError()

    @property
    def fromPort(self) -> _pib.PortItemBase:
        return self._fromPort

    @property
    def toPort(self) -> _pib.PortItemBase:
        return self._toPort

    def _updateModels(self, newDisplayName: str) -> None:
        raise NotImplementedError()

    def _createSegmentItem(self, startNode, endNode):
        raise NotImplementedError()

    def isVisible(self):
        res = True
        for s in self.segments:  # pylint: disable = invalid-name
            if not s.isVisible():
                res = False

        return res

    def setDisplayName(self, newName: str) -> None:
        self.displayName = newName
        self.updateSegLabels()
        self._updateModels(newName)

    def setLabelPos(self, tup: _tp.Tuple[float, float]) -> None:
        pos = self._toPoint(tup)

        assert self.firstS

        self.firstS.label.setPos(pos)

    def setMassLabelPos(self, tup: _tp.Tuple[float, float]) -> None:
        pos = self._toPoint(tup)

        assert self.firstS

        self.firstS.labelMass.setPos(pos)

    @staticmethod
    def _toPoint(tup):
        pos = _qtc.QPointF(tup[0], tup[1])
        return pos

    def setStartPort(self, newStartPort):
        self._fromPort = newStartPort
        self.startPos = newStartPort.scenePos()

    def setEndPort(self, newEndPort):
        self._toPort = newEndPort

    def setStartPos(self):
        pass

    def setEndPos(self):
        pass

    def setColor(self, value, **kwargs):
        if "mfr" in kwargs:
            if kwargs["mfr"] == "NegMfr":
                col = _qtg.QColor(0, 0, 255)
            elif kwargs["mfr"] == "ZeroMfr":
                col = _qtg.QColor(142, 142, 142)  # Gray
            elif kwargs["mfr"] == "min":
                col = _qtg.QColor(0, 0, 204)  # deep blue
            elif kwargs["mfr"] == "max":
                col = _qtg.QColor(153, 0, 0)  # deep red
            elif kwargs["mfr"] == "minTo25":
                col = _qtg.QColor(0, 128, 255)  # blue
            elif kwargs["mfr"] == "25To50":
                col = _qtg.QColor(102, 255, 255)  # light blue
            elif kwargs["mfr"] == "50To75":
                col = _qtg.QColor(255, 153, 153)  # light red
            elif kwargs["mfr"] == "75ToMax":
                col = _qtg.QColor(255, 51, 51)  # red
            else:
                col = _qtg.QColor(255, 0, 0)

            for s in self.segments:  # pylint: disable = invalid-name
                self.logger.debug("Value: " + str(value))
                s.setColorAndWidthAccordingToMassflow(col, value)

        else:
            self.logger.debug("No color to set in Connection.setColor()")

    # Getters
    def getStartPoint(self):
        return _qtc.QPointF(self.fromPort.scenePos())

    def getEndPoint(self):
        return _qtc.QPointF(self.toPort.scenePos())

    def getNodePos(self, searchCorner):

        corners = self.getCorners()

        for i, corner in enumerate(corners):
            if corner == searchCorner:
                return i
        self.logger.debug("corner not found is " + str(searchCorner))

        return 0

    def getFirstSeg(self):
        return self.segments[0]

    def getCorners(self):
        res = []

        tempNode = self.startNode.nextN()

        while tempNode.nextN() is not None:
            res.append(tempNode.parent)
            tempNode = tempNode.nextN()

        return res

    def switchPorts(self):
        temp = self.fromPort
        self._fromPort = self.toPort
        self._toPort = temp

    # Initialization
    def initNew(self, parent):

        self.parent = parent

        if self.parent.editorMode == 0:
            self.logger.debug("Creating a new connection in mode 0")
            self._initializeSegmentMode0()
        elif self.parent.editorMode == 1:
            self.logger.debug("Creating a new connection in mode 1")
            self._initializeSegmentsMode1()
        else:
            self.logger.debug("No valid mode during creating of connection")

    def _initializeSegmentMode0(self):
        self.startNode.setNext(self.endNode)
        self.endNode.setPrev(self.startNode)

        self.firstS = self._createSegmentItem(self.startNode, self.endNode)
        self.firstS.setLine(self.getStartPoint(), self.getEndPoint())

        self.updateSegmentGradients()

        self.positionLabel()

    def _initializeSegmentsMode1(self):
        self._createSegmentsMode1()
        self.updateSegmentGradients()
        self.positionLabel()

    def _loadSegments(self, segmentsCorners):
        self._clearConnection()

        tempNode = self.startNode

        rad = self.getRadius()

        for segmentsCorner in segmentsCorners:
            cor = _ci.CornerItem(-rad, -rad, 2 * rad, 2 * rad, tempNode, tempNode.nextN(), self)

            cor.setPos(float(segmentsCorner[0]), float(segmentsCorner[1]))
            cor.setFlag(cor.ItemSendsScenePositionChanges, True)

            cor.setZValue(100)
            cor.setVisible(True)

            cor.node.nextNode.setPrev(cor.node)
            cor.node.prevNode.setNext(cor.node)
            self._createSegmentItem(tempNode, cor.node)

            tempNode = cor.node

        self._createSegmentItem(tempNode, tempNode.nextN())

        for segment in self.segments:  # pylint: disable = invalid-name
            pos1 = None
            pos2 = None

            if isinstance(segment.startNode.parent, ConnectionBase) and segment.startNode.prevNode is None:
                pos1 = (
                    segment.startNode.parent.fromPort.scenePos().x(),
                    segment.startNode.parent.fromPort.scenePos().y(),
                )
            if isinstance(segment.endNode.parent, ConnectionBase) and segment.endNode.nextNode is None:
                pos2 = segment.endNode.parent.toPort.scenePos().x(), segment.endNode.parent.toPort.scenePos().y()

            if isinstance(segment.startNode.parent, _ci.CornerItem):
                pos1 = segment.startNode.parent.scenePos().x(), segment.startNode.parent.scenePos().y()
            if isinstance(segment.endNode.parent, _ci.CornerItem):
                pos2 = segment.endNode.parent.scenePos().x(), segment.endNode.parent.scenePos().y()

            segment.setLine(pos1[0], pos1[1], pos2[0], pos2[1])

        self.firstS = self.segments[0]

        self.updateSegmentGradients()
        self.positionLabel()

    # Label related
    def setLabelVisible(self, isVisible: bool) -> None:
        assert self.firstS
        self.firstS.setLabelVisible(isVisible)

    def toggleLabelVisible(self) -> None:
        assert self.firstS
        self.firstS.toggleLabelVisible()

    def updateSegLabels(self):
        for s in self.segments:  # pylint: disable = invalid-name
            s.label.setPlainText(self.displayName)

    def positionLabel(self):
        self.firstS.label.setPos(self.getStartPoint())
        self.firstS.labelMass.setPos(self.getStartPoint())
        self.rotateLabel()

    def rotateLabel(self):
        angle = 0 if self.firstS.isHorizontal() else 90
        self.firstS.label.setRotation(angle)

    def setMassFlowLabelVisible(self, isVisible: bool) -> None:
        assert self.firstS
        self.firstS.setMassFlowLabelVisible(isVisible)

    def toggleMassFlowLabelVisible(self) -> None:
        assert self.firstS
        self.firstS.toggleMassFlowLabelVisible()

    def getRadius(self):
        raise NotImplementedError()

    # Makes 90deg angles of connection
    def _createSegmentsMode1(self):  # pylint: disable = too-many-locals, too-many-statements
        rad = self.getRadius()

        if (self.fromPort.side == 2) and (self.toPort.side == 2):
            self.fromPort.createdAtSide = 2
            self.toPort.createdAtSide = 2
            portOffset = 30

            corner1 = _ci.CornerItem(-rad, -rad, 2 * rad, 2 * rad, self.startNode, None, self)
            corner2 = _ci.CornerItem(-rad, -rad, 2 * rad, 2 * rad, corner1.node, None, self)
            corner3 = _ci.CornerItem(-rad, -rad, 2 * rad, 2 * rad, corner2.node, None, self)
            corner4 = _ci.CornerItem(-rad, -rad, 2 * rad, 2 * rad, corner3.node, self.endNode, self)

            corner1.node.setNext(corner2.node)
            corner2.node.setNext(corner3.node)
            corner3.node.setNext(corner4.node)

            seg1 = self._createSegmentItem(self.startNode, corner1.node)
            seg2 = self._createSegmentItem(corner1.node, corner2.node)
            seg3 = self._createSegmentItem(corner2.node, corner3.node)
            seg4 = self._createSegmentItem(corner3.node, corner4.node)
            seg5 = self._createSegmentItem(corner4.node, self.endNode)

            self.startNode.setNext(corner1.node)
            self.endNode.setPrev(corner4.node)

            pos1 = self.fromPort.scenePos()
            pos2 = self.toPort.scenePos()

            baseLineHeight = max(pos1.y(), pos2.y()) + 100.6

            p1 = _qtc.QPointF(pos1.x() + portOffset, pos1.y())  # pylint: disable = invalid-name
            p2 = _qtc.QPointF(p1.x(), baseLineHeight)  # pylint: disable = invalid-name
            p3 = _qtc.QPointF(pos2.x() + portOffset, baseLineHeight)  # pylint: disable = invalid-name
            p4 = _qtc.QPointF(p3.x(), pos2.y())  # pylint: disable = invalid-name

            seg1.setLine(pos1, p1)
            seg2.setLine(p1, p2)
            seg3.setLine(p2, p3)
            seg4.setLine(p3, p4)
            seg5.setLine(p4, pos2)

            corner1.setFlag(corner1.ItemSendsScenePositionChanges, True)
            corner2.setFlag(corner2.ItemSendsScenePositionChanges, True)
            corner3.setFlag(corner3.ItemSendsScenePositionChanges, True)
            corner4.setFlag(corner4.ItemSendsScenePositionChanges, True)

            corner1.setZValue(100)
            corner2.setZValue(100)
            corner3.setZValue(100)
            corner4.setZValue(100)

            corner1.setPos(p1)
            corner2.setPos(p2)
            corner3.setPos(p3)
            corner4.setPos(p4)

        elif (self.fromPort.side == 0) and (self.toPort.side == 0):
            self.fromPort.createdAtSide = 0
            self.toPort.createdAtSide = 0
            portOffset = 30

            corner1 = _ci.CornerItem(-rad, -rad, 2 * rad, 2 * rad, self.startNode, None, self)
            corner2 = _ci.CornerItem(-rad, -rad, 2 * rad, 2 * rad, corner1.node, None, self)
            corner3 = _ci.CornerItem(-rad, -rad, 2 * rad, 2 * rad, corner2.node, None, self)
            corner4 = _ci.CornerItem(-rad, -rad, 2 * rad, 2 * rad, corner3.node, self.endNode, self)

            corner1.node.setNext(corner2.node)
            corner2.node.setNext(corner3.node)
            corner3.node.setNext(corner4.node)

            seg1 = self._createSegmentItem(self.startNode, corner1.node)
            seg2 = self._createSegmentItem(corner1.node, corner2.node)
            seg3 = self._createSegmentItem(corner2.node, corner3.node)
            seg4 = self._createSegmentItem(corner3.node, corner4.node)
            seg5 = self._createSegmentItem(corner4.node, self.endNode)

            self.startNode.setNext(corner1.node)
            self.endNode.setPrev(corner4.node)

            pos1 = self.fromPort.scenePos()
            pos2 = self.toPort.scenePos()

            baseLineHeight = max(pos1.y(), pos2.y()) + 100.6

            p1 = _qtc.QPointF(pos1.x() - portOffset, pos1.y())  # pylint: disable = invalid-name
            p2 = _qtc.QPointF(p1.x(), baseLineHeight)  # pylint: disable = invalid-name
            p3 = _qtc.QPointF(pos2.x() - portOffset, baseLineHeight)  # pylint: disable = invalid-name
            p4 = _qtc.QPointF(p3.x(), pos2.y())  # pylint: disable = invalid-name

            seg1.setLine(pos1, p1)
            seg2.setLine(p1, p2)
            seg3.setLine(p2, p3)
            seg4.setLine(p3, p4)
            seg5.setLine(p4, pos2)

            corner1.setFlag(corner1.ItemSendsScenePositionChanges, True)
            corner2.setFlag(corner2.ItemSendsScenePositionChanges, True)
            corner3.setFlag(corner3.ItemSendsScenePositionChanges, True)
            corner4.setFlag(corner4.ItemSendsScenePositionChanges, True)

            corner1.setZValue(100)
            corner2.setZValue(100)
            corner3.setZValue(100)
            corner4.setZValue(100)

            corner1.setPos(p1)
            corner2.setPos(p2)
            corner3.setPos(p3)
            corner4.setPos(p4)

        elif self.fromPort.side == 1:
            self.fromPort.createdAtSide = 1
            # pylint: disable = fixme
            # todo :  when rotated, it cause a problem because side gets changed

            pos1 = self.fromPort.scenePos()
            pos2 = self.toPort.scenePos()

            if pos2.y() <= pos1.y():
                corner1 = _ci.CornerItem(-rad, -rad, 2 * rad, 2 * rad, self.startNode, self.endNode, self)

                seg1 = self._createSegmentItem(self.startNode, corner1.node)
                seg2 = self._createSegmentItem(corner1.node, self.endNode)

                self.startNode.setNext(corner1.node)
                self.endNode.setPrev(corner1.node)

                # position of the connecting node
                p1 = _qtc.QPointF(pos1.x(), pos2.y() - 0.333)  # pylint: disable = invalid-name

                seg1.setLine(pos1, p1)
                seg2.setLine(p1, pos2)

                corner1.setFlag(corner1.ItemSendsScenePositionChanges, True)
                corner1.setZValue(100)
                self.fromPort.setZValue(100)
                self.toPort.setZValue(100)

                corner1.setPos(p1)
            else:
                corner1 = _ci.CornerItem(-rad, -rad, 2 * rad, 2 * rad, self.startNode, None, self)
                corner2 = _ci.CornerItem(-rad, -rad, 2 * rad, 2 * rad, corner1.node, self.endNode, self)

                corner1.node.setNext(corner2.node)

                seg1 = self._createSegmentItem(self.startNode, corner1.node)
                seg2 = self._createSegmentItem(corner1.node, corner2.node)
                seg3 = self._createSegmentItem(corner2.node, self.endNode)

                self.startNode.setNext(corner1.node)
                self.endNode.setPrev(corner2.node)

                offsetPoint = pos1.y() - 15.666

                helperPoint1 = _qtc.QPointF(pos1.x(), offsetPoint)  # pylint: disable = invalid-name
                helperPoint2 = _qtc.QPointF(pos2.x(), offsetPoint)  # pylint: disable = invalid-name

                seg1.setLine(pos1, helperPoint1)
                seg2.setLine(helperPoint1, helperPoint2)
                seg3.setLine(helperPoint2, pos2)

                corner1.setFlag(corner1.ItemSendsScenePositionChanges, True)
                corner2.setFlag(corner2.ItemSendsScenePositionChanges, True)

                corner1.setZValue(100)
                corner2.setZValue(100)
                self.fromPort.setZValue(100)
                self.toPort.setZValue(100)

                corner1.setPos(helperPoint1)
                corner2.setPos(helperPoint2)

        elif self.fromPort.side == 3:
            self.fromPort.createdAtSide = 3

            pos1 = self.fromPort.scenePos()
            pos2 = self.toPort.scenePos()

            if pos2.y() >= pos1.y():
                corner1 = _ci.CornerItem(-rad, -rad, 2 * rad, 2 * rad, self.startNode, self.endNode, self)

                seg1 = self._createSegmentItem(self.startNode, corner1.node)
                seg2 = self._createSegmentItem(corner1.node, self.endNode)

                self.startNode.setNext(corner1.node)
                self.endNode.setPrev(corner1.node)

                # position of the connecting node
                p1 = _qtc.QPointF(pos1.x(), pos2.y() - 0.333)  # pylint: disable = invalid-name

                seg1.setLine(pos1, p1)
                seg2.setLine(p1, pos2)

                corner1.setFlag(corner1.ItemSendsScenePositionChanges, True)
                corner1.setZValue(100)
                self.fromPort.setZValue(100)
                self.toPort.setZValue(100)

                corner1.setPos(p1)
            else:
                corner1 = _ci.CornerItem(-rad, -rad, 2 * rad, 2 * rad, self.startNode, None, self)
                corner2 = _ci.CornerItem(-rad, -rad, 2 * rad, 2 * rad, corner1.node, self.endNode, self)

                corner1.node.setNext(corner2.node)

                seg1 = self._createSegmentItem(self.startNode, corner1.node)
                seg2 = self._createSegmentItem(corner1.node, corner2.node)
                seg3 = self._createSegmentItem(corner2.node, self.endNode)

                self.startNode.setNext(corner1.node)
                self.endNode.setPrev(corner2.node)

                offsetPoint = pos1.y() + 15.666

                helperPoint1 = _qtc.QPointF(pos1.x(), offsetPoint)  # pylint: disable = invalid-name
                helperPoint2 = _qtc.QPointF(pos2.x(), offsetPoint)  # pylint: disable = invalid-name

                seg1.setLine(pos1, helperPoint1)
                seg2.setLine(helperPoint1, helperPoint2)
                seg3.setLine(helperPoint2, pos2)

                corner1.setFlag(corner1.ItemSendsScenePositionChanges, True)
                corner2.setFlag(corner2.ItemSendsScenePositionChanges, True)

                corner1.setZValue(100)
                corner2.setZValue(100)
                self.fromPort.setZValue(100)
                self.toPort.setZValue(100)

                corner1.setPos(helperPoint1)
                corner2.setPos(helperPoint2)

        else:
            pos1 = self.fromPort.scenePos()
            pos2 = self.toPort.scenePos()

            self.fromPort.createdAtSide = self.fromPort.side
            self.toPort.createdAtSide = self.toPort.side

            corner1 = _ci.CornerItem(-rad, -rad, 2 * rad, 2 * rad, self.startNode, None, self)
            corner2 = _ci.CornerItem(-rad, -rad, 2 * rad, 2 * rad, corner1.node, self.endNode, self)

            corner1.node.setNext(corner2.node)

            seg1 = self._createSegmentItem(self.startNode, corner1.node)
            seg2 = self._createSegmentItem(corner1.node, corner2.node)
            seg3 = self._createSegmentItem(corner2.node, self.endNode)

            self.startNode.setNext(corner1.node)
            self.endNode.setPrev(corner2.node)

            midx = pos1.x() + 0.5 * (pos2.x() - pos1.x())

            seg1.setLine(pos1.x(), pos1.y(), midx, pos1.y())
            seg2.setLine(midx, pos1.y(), midx, pos2.y())
            seg3.setLine(midx, pos2.y(), pos2.x(), pos2.y())

            corner1.setFlag(corner1.ItemSendsScenePositionChanges, True)
            corner2.setFlag(corner2.ItemSendsScenePositionChanges, True)

            corner1.setZValue(100)
            corner2.setZValue(100)
            self.toPort.setZValue(100)
            self.fromPort.setZValue(100)

            helperPoint1 = _qtc.QPointF(midx, pos1.y())  # pylint: disable = invalid-name
            helperPoint2 = _qtc.QPointF(midx, pos2.y())  # pylint: disable = invalid-name

            corner1.setPos(helperPoint1)
            corner2.setPos(helperPoint2)

        self.firstS = self.getFirstSeg()

    def _clearConnection(self):
        _cdel.deleteChildGraphicsItems(self)

        self.segments.clear()

        self.startNode.setNext(self.endNode)
        self.endNode.setPrev(self.startNode)

    def deleteConnection(self):
        self.fromPort.connectionList.remove(self)
        self.toPort.connectionList.remove(self)

        self.parent.trnsysObj.remove(self)
        self.parent.connectionList.remove(self)

    def createDeleteUndoCommandAndAddToStack(self) -> None:
        deleteConnectionCommand = self.createDeleteUndoCommand()
        self.parent.parent().undoStack.push(deleteConnectionCommand)

    def createDeleteUndoCommand(self, parentCommand: _tp.Optional[_qtw.QUndoCommand] = None) -> _qtw.QUndoCommand:
        raise NotImplementedError()

    # Gradient related
    def totalLength(self):
        summedLength = 0

        for segment in self.segments:
            summedLength += calcDist(segment.line().p1(), segment.line().p2())
        return summedLength

    def partialLength(self, node):
        # Returns the cummulative length of line up to given node
        # Assumes that segments is ordered correctly!
        res = 0
        if node == self.startNode:
            return res

        for i in self.segments:
            res += calcDist(i.line().p1(), i.line().p2())
            if i.endNode == node:
                break

        return res

    def updateSegmentGradients(self):
        for segment in self.segments:
            segment.resetLinePens()

    # Invert connection
    def invertConnection(self):
        # Invert segment list
        self.segments.reverse()

        # Invert nodes
        self.invertNodes()

        # Invert ports
        temp = self.toPort
        self._toPort = self.fromPort
        self._fromPort = temp

        startingNode = self.startNode
        self.startNode = self.endNode
        self.endNode = startingNode

        for s in self.segments:  # pylint: disable = invalid-name
            temp2 = s.startNode
            s.startNode = s.endNode
            s.endNode = temp2

            temp3 = s.firstChild
            s.firstChild = s.secondChild
            s.secondChild = temp3

            s.setLine(s.line().p2().x(), s.line().p2().y(), s.line().p1().x(), s.line().p1().y())

            s.resetLinePens()

    def invertNodes(self):
        element = self.startNode

        while element.nextN() is not None:
            temp = element.nextN()
            previousNode = element.prevN()
            nextNode = element.nextN()

            element.setNext(previousNode)
            element.setPrev(nextNode)
            element = temp

        previousNode = element.prevN()
        nextNode = element.nextN()
        element.setNext(previousNode)
        element.setPrev(nextNode)

    def selectConnection(self):
        self.isConnectionSelected = True

        for segment in self.segments:
            segment.resetLinePens()

        self.setLabelsSelected(True)

    def deselectConnection(self):
        self.isConnectionSelected = False

        for segment in self.segments:
            segment.resetLinePens()

        self.setLabelsSelected(False)

    def setLabelsSelected(self, isSelected: bool) -> None:
        assert self.firstS
        self._setBold(self.firstS.label, isSelected)
        self._setBold(self.firstS.labelMass, isSelected)

    @staticmethod
    def _setBold(label: _qtw.QGraphicsTextItem, isBold: bool) -> None:
        originalFontCopy = label.font()
        originalFontCopy.setBold(isBold)
        label.setFont(originalFontCopy)

    def printConnNodes(self):
        self.logger.debug("These are the nodes: ")

        element = self.startNode
        while element.nextN() is not None:
            self.logger.debug(
                "Node is "
                + str(element)
                + " has nextNode "
                + str(element.nextN())
                + " has pL "
                + str(self.partialLength(element))
            )
            element = element.nextN()

        self.logger.debug("Node is " + str(element) + " has nextNode " + str(element.nextN()))

    def printConnSegs(self):
        self.logger.debug("These are the segments in order")
        for s in self.segments:  # pylint: disable = invalid-name
            self.logger.debug(
                "Segment is "
                + str(s)
                + " has global id "
                + str(s.id)
                + " has startnode "
                + str(s.startNode)
                + " endnode "
                + str(s.endNode)
            )

    # Saving / Loading
    def encode(self):
        raise NotImplementedError()

    def decode(self, i):
        raise NotImplementedError()

    def exportPumpOutlets(self):
        return "", 0

    def exportMassFlows(self):
        return "", 0

    def exportDivSetting1(self):
        return "", 0

    def exportDivSetting2(self, nUnit):
        return "", nUnit

    def getInternalPiping(self) -> _ip.InternalPiping:
        raise NotImplementedError()

    def exportPipeAndTeeTypesForTemp(self, startingUnit):
        raise NotImplementedError()

    def findStoragePort(self, virtualBlock):
        portToPrint = None
        for port in virtualBlock.inputs + virtualBlock.outputs:
            if self in port.connectionList:
                # Found the port of the generated block adjacent to this pipe
                # Assumes 1st connection is with storageTank
                if self.fromPort == port:
                    if self.toPort.connectionList[0].fromPort == self.toPort:
                        portToPrint = self.toPort.connectionList[0].toPort
                    else:
                        portToPrint = self.toPort.connectionList[0].fromPort
                else:
                    if self.fromPort.connectionList[0].fromPort == self.fromPort:
                        portToPrint = self.fromPort.connectionList[0].toPort
                    else:
                        portToPrint = self.fromPort.connectionList[0].fromPort
        return portToPrint

    def assignIDsToUninitializedValuesAfterJsonFormatMigration(self, generator: _id.IdGenerator) -> None:
        pass
