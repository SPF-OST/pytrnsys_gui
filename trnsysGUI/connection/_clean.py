from __future__ import annotations

import typing as _tp

import PyQt5.QtWidgets as _qtw

import trnsysGUI.connection.delete as _cdelete
import trnsysGUI.cornerItem as _ci
import trnsysGUI.segments.node as _node
import trnsysGUI.segments.segmentItemBase as _sib

if _tp.TYPE_CHECKING:  # pragma: no cover
    import trnsysGUI.connection.connectionBase as _cb


def removeUnnecessarySegments(
    segments: _tp.Sequence[_sib.SegmentItemBase],
) -> _tp.Sequence[_sib.SegmentItemBase]:
    remainingIntermediateSegments = (
        _removeUnnecessaryIntermediateSegmentsFromSceneAndGetRemaining(
            segments
        )
    )

    isHorizontal = _isHorizontal(segments)

    firstSegment = segments[0]
    lastSegment = segments[-1]

    newSegments = _possiblyMergeLastTwoSegments(
        firstSegment, remainingIntermediateSegments, lastSegment, isHorizontal
    )

    return newSegments


def _removeUnnecessaryIntermediateSegmentsFromSceneAndGetRemaining(
    segments: _tp.Sequence[_sib.SegmentItemBase],
) -> _tp.Sequence[_sib.SegmentItemBase]:
    if _isHorizontal(segments):
        assert len(segments) >= 3

    intermediateSegments = segments[1:-1]
    remainingIntermediateSegments = [intermediateSegments[0]]
    for currentSegment in intermediateSegments[1:]:
        previousSegment = remainingIntermediateSegments[-1]

        if _isTrulyVertical(previousSegment) or _isTrulyVertical(
            currentSegment
        ):
            remainingIntermediateSegments.append(currentSegment)
            continue

        _removeFromScene(previousSegment, segmentToDelete=currentSegment)

    return remainingIntermediateSegments


def _possiblyMergeLastTwoSegments(
    firstSegment: _sib.SegmentItemBase,
    remainingIntermediateSegments: _tp.Sequence[_sib.SegmentItemBase],
    lastSegment: _sib.SegmentItemBase,
    isHorizontal: bool,
) -> _tp.Sequence[_sib.SegmentItemBase]:
    lastRemainingIntermediate = remainingIntermediateSegments[-1]

    areLastTwoSegmentsHorizontal = (
        lastRemainingIntermediate.isHorizontal() and lastSegment.isHorizontal()
    )

    canMergeLastTwoSegments = areLastTwoSegmentsHorizontal
    if isHorizontal:
        # We must guarantee the invariant _isHorizontal(segments) => len(segments) >= 3
        canMergeLastTwoSegments &= len(remainingIntermediateSegments) > 1

    if not canMergeLastTwoSegments:
        newSegments = [
            firstSegment,
            *remainingIntermediateSegments,
            lastSegment,
        ]
    else:
        _removeFromScene(lastRemainingIntermediate, lastSegment)
        newAllButLastSegments = remainingIntermediateSegments

        newSegments = [firstSegment, *newAllButLastSegments]

    return newSegments


def _removeFromScene(
    previousSegment: _sib.SegmentItemBase,
    segmentToDelete: _sib.SegmentItemBase,
) -> None:
    endPortOrCornerItem = _getPortOrCornerItem(segmentToDelete.endNode)

    previousLine = previousSegment.line()
    previousEndCorner = previousSegment.endNode.parent

    newEndNode = segmentToDelete.endNode
    previousSegment.setEndNode(newEndNode)

    previousSegment.setLine(previousLine.p1(), endPortOrCornerItem.scenePos())

    _cdelete.deleteGraphicsItem(previousEndCorner)
    _cdelete.deleteChildGraphicsItems(segmentToDelete)


def _isHorizontal(segments: _tp.Sequence[_sib.SegmentItemBase]) -> bool:
    return all(s.isHorizontal() for s in segments)


def _isTrulyVertical(segment: _sib.SegmentItemBase) -> bool:
    return not segment.isZeroLength() and segment.isVertical()


def _getPortOrCornerItem(node: _node.Node) -> _qtw.QGraphicsItem:
    parent = node.parent

    if isinstance(parent, _ci.CornerItem):
        return parent

    # Unfortunately, a start or end `Node`'s parent is a `ConnectionBase` not the port itself.
    # However, we can't `import` `ConnectionBase` here as that would lead to a circular import.
    # That's why the below `hasattr` hack. I'd say a start or end `Node`'s parent should be the
    # `PortItem` directly. That would also be similar to intermediate nodes whose parents are the
    # `CornerItem`s.
    if hasattr(parent, "fromPort") and hasattr(parent, "toPort"):
        connection: _cb.ConnectionBase = parent

        if node == connection.startNode:
            return connection.fromPort

        if node == connection.endNode:
            return connection.toPort

    raise AssertionError("Shouldn't get here.")
