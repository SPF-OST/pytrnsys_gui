# pylint: disable = too-many-lines

from __future__ import annotations

import math as _math
import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtWidgets as _qtw

import trnsysGUI.cornerItem as _ci
import trnsysGUI.PortItemBase as _pib
import trnsysGUI.connection.delete as _cdel
import trnsysGUI.connection.values as _values
import trnsysGUI.idGenerator as _id
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.segments.node as _node
import trnsysGUI.segments.segmentItemBase as _sib
from . import _clean

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

        self._label = _qtw.QGraphicsTextItem(self.displayName, parent=self)
        self._label.setVisible(False)
        self._label.setFlag(self.ItemIsMovable, True)

        self.massFlowLabel = _qtw.QGraphicsTextItem(parent=self)
        self.massFlowLabel.setVisible(False)
        self.massFlowLabel.setFlag(self.ItemIsMovable, True)

        self.startPos = None

        self._draggedSegment: _tp.Optional[_sib.SegmentItemBase] = None

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

    @classmethod
    @_tp.override
    def hasDdckPlaceHolders(cls) -> bool:
        return False

    @classmethod
    @_tp.override
    def shallRenameOutputTemperaturesInHydraulicFile(cls) -> bool:
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
        self._label.setPlainText(self.displayName)
        self._updateModels(newName)

    def setLabelPos(self, tup: _tp.Tuple[float, float]) -> None:
        pos = self._toPoint(tup)
        self._label.setPos(pos)

    def setMassLabelPos(self, tup: _tp.Tuple[float, float]) -> None:
        pos = self._toPoint(tup)
        self.massFlowLabel.setPos(pos)

    @staticmethod
    def _toPoint(tup):
        pos = _qtc.QPointF(tup[0], tup[1])
        return pos

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

    def getPreviousAndNextSegment(
        self, intermediateNode: _node.Node
    ) -> _tp.Tuple[_sib.SegmentItemBase, _sib.SegmentItemBase]:
        previousSegment: _sib.SegmentItemBase
        nextSegment: _sib.SegmentItemBase

        previousAndNextSegments = zip(self.segments[:-1], self.segments[1:], strict=True)
        for previousSegment, nextSegment in previousAndNextSegments:
            if previousSegment.endNode == intermediateNode and nextSegment.startNode == intermediateNode:
                return previousSegment, nextSegment

        raise ValueError("Node is not an intermediate node of connection.")

    def getCorners(self):
        res = []

        tempNode = self.startNode.nextN()

        while tempNode.nextN() is not None:
            res.append(tempNode.parent)
            tempNode = tempNode.nextN()

        return res

    # Initialization
    def initNew(self, parent):

        self.parent = parent

        self._initializeSegments()

    def _initializeSegments(self):
        self._createSegments()
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

            assert pos1 and pos2

            segment.setLine(pos1[0], pos1[1], pos2[0], pos2[1])  # /NOSONAR

        self.updateSegmentGradients()
        self.rotateLabel()

    # Label related
    def setLabelVisible(self, isVisible: bool) -> None:
        self._label.setVisible(isVisible)

    def toggleLabelVisible(self) -> None:
        wasVisible = self._label.isVisible()
        self._label.setVisible(not wasVisible)

    def positionLabel(self):
        self._label.setPos(self.getStartPoint())
        self.massFlowLabel.setPos(self.getStartPoint())
        self.rotateLabel()

    def rotateLabel(self):
        angle = 0 if self.segments[0].isHorizontal() else 90
        self._label.setRotation(angle)

    def toggleMassFlowLabelVisible(self) -> None:
        wasVisible = self.massFlowLabel.isVisible()
        self.massFlowLabel.setVisible(not wasVisible)

    def getRadius(self):
        raise NotImplementedError()

    # Makes 90deg angles of connection
    def _createSegments(self):  # pylint: disable = too-many-locals, too-many-statements
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

    def _clearConnection(self):
        labels = [self._label, self.massFlowLabel]
        _cdel.deleteChildGraphicsItems(self, exclude=labels)

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
        # Returns the cumulative length of line up to given node
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
        self._setBold(self._label, isSelected)
        self._setBold(self.massFlowLabel, isSelected)

    @staticmethod
    def _setBold(label: _qtw.QGraphicsTextItem, isBold: bool) -> None:
        originalFontCopy = label.font()
        originalFontCopy.setBold(isBold)
        label.setFont(originalFontCopy)

    # Saving / Loading
    def encode(self):
        raise NotImplementedError()

    def decode(self, i):
        raise NotImplementedError()

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

    def assignIDsToUninitializedValuesAfterJsonFormatMigration(self, generator: _id.IdGenerator) -> None:
        pass

    def onMousePressed(self, segment: _sib.SegmentItemBase, event: _qtw.QGraphicsSceneMouseEvent) -> None:
        if event.button() != _qtc.Qt.LeftButton:
            return

        self.selectConnection()

        if segment.isIntermediateSegment():
            self._draggedSegment = segment
            return

        assert segment.isFirstOrLastSegment()

        if segment.isVertical():
            # Dragging of vertical first or last segment not yet supported
            return

        rad = self.getRadius()

        secondCorner = _ci.CornerItem(-rad, -rad, 2 * rad, 2 * rad, segment.startNode, None, self)
        thirdCorner = _ci.CornerItem(-rad, -rad, 2 * rad, 2 * rad, secondCorner.node, segment.endNode, self)

        secondCorner.setFlag(_qtw.QGraphicsItem.ItemSendsScenePositionChanges)
        thirdCorner.setFlag(_qtw.QGraphicsItem.ItemSendsScenePositionChanges)

        secondCorner.node.setNext(thirdCorner.node)

        segment.startNode.setNext(secondCorner.node)
        segment.endNode.setPrev(thirdCorner.node)

        if segment.isFirstSegment():
            segment.endNode = secondCorner.node

            firstAdditionalSegment = self._createSegmentItem(secondCorner.node, thirdCorner.node)
            secondAdditionalSegment = self._createSegmentItem(thirdCorner.node, thirdCorner.node.nextN())
        else:
            segment.startNode = thirdCorner.node

            firstAdditionalSegment = self._createSegmentItem(secondCorner.node.prevN(), secondCorner.node)
            secondAdditionalSegment = self._createSegmentItem(secondCorner.node, thirdCorner.node)

        secondCorner.setZValue(100)
        thirdCorner.setZValue(100)
        firstAdditionalSegment.setZValue(1)
        secondAdditionalSegment.setZValue(1)

        secondCorner.setVisible(True)
        thirdCorner.setVisible(True)

        firstAdditionalSegment.setVisible(True)
        secondAdditionalSegment.setVisible(True)

        newPos = event.scenePos()
        if segment.isFirstSegment():
            secondCorner.setPos(newPos.x() - 10, self.fromPort.scenePos().y())

            thirdCorner.setPos(newPos.x() - 10, newPos.y())

            nextCorner = thirdCorner.node.nextN().parent
            nextCorner.setY(newPos.y())

            self._draggedSegment = secondAdditionalSegment

        else:
            previousCorner = secondCorner.node.prevN().parent
            previousCorner.setY(newPos.y())

            secondCorner.setPos(newPos.x() + 10, newPos.y())

            thirdCorner.setPos(newPos.x() + 10, self.toPort.scenePos().y())

            self._draggedSegment = firstAdditionalSegment

        self._assertSegmentsAreConsistent()

    def onMouseMoved(self, event: _qtw.QGraphicsSceneMouseEvent) -> None:
        if not self._draggedSegment:
            return

        assert self._draggedSegment.isIntermediateSegment()

        newPos = event.scenePos()

        self._dragIntermediateSegment(newPos)

    def onMouseReleased(self, event: _qtw.QGraphicsSceneMouseEvent) -> None:
        if event.button() != _qtc.Qt.LeftButton:
            return

        if not self._draggedSegment:
            return

        self._draggedSegment = None

        self._removeUnnecessarySegments()

        self._assertSegmentsAreConsistent()

    def _dragIntermediateSegment(self, newPos: _qtc.QPointF) -> None:
        assert self._draggedSegment
        assert self._draggedSegment.isIntermediateSegment()

        startCorner = self._draggedSegment.startNode.parent
        endCorner = self._draggedSegment.endNode.parent

        startPos = startCorner.scenePos()
        endPos = endCorner.scenePos()

        if self._draggedSegment.isVertical():
            startCorner.setPos(newPos.x(), startPos.y())
            endCorner.setPos(newPos.x(), endPos.y())

        if self._draggedSegment.isHorizontal():
            startCorner.setPos(startPos.x(), newPos.y())
            endCorner.setPos(endPos.x(), newPos.y())

    def _removeUnnecessarySegments(self) -> None:
        isHorizontal = self._isHorizontal()

        # We must guarantee the invariant self._isHorizontal() => len(self.segments) >= 3
        if not isHorizontal or len(self.segments) >= 3:
            newSegments = _clean.removeUnnecessarySegments(self.segments)

            self.segments = list(newSegments)

        if isHorizontal and len(self.segments) == 3:
            self._recenterVerticalConnection()

    def _recenterVerticalConnection(self) -> None:
        assert len(self.segments) == 3, "Can only recenter connections with three segments."

        intermediateSegment = self.segments[1]

        fromPos = self.fromPort.scenePos()
        toPos = self.toPort.scenePos()

        midPoint = fromPos + 0.5 * (toPos - fromPos)  # type: ignore[operator]

        intermediateSegment.startNode.parent.setPos(midPoint)
        intermediateSegment.endNode.parent.setPos(midPoint)

    def _isHorizontal(self):
        return all(s.isHorizontal() for s in self.segments)

    def _assertSegmentsAreConsistent(self):
        if self._isHorizontal():
            assert len(self.segments) >= 3, "Horizontal segments must always have 3 or more segments."

        firstSegment = self.segments[0]
        assert firstSegment.isFirstSegment()

        lastSegment = self.segments[-1]
        assert lastSegment.isLastSegment()

        startNode = self.startNode
        assert startNode
        assert startNode == firstSegment.startNode
        assert not startNode.prevN()
        assert startNode.parent == self

        endNode = self.endNode
        assert endNode
        assert endNode == lastSegment.endNode
        assert not endNode.nextN()
        assert endNode.parent == self

        for segment in self.segments:
            endNode = startNode.nextN()
            assert endNode
            assert endNode.prevN() == startNode

            if segment != lastSegment:
                assert isinstance(endNode.parent, _ci.CornerItem)

            assert segment.startNode == startNode
            assert segment.endNode == endNode

            startNode = endNode

        lastEndNode = endNode
        assert lastEndNode == lastSegment.endNode
