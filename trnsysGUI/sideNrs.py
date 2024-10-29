import typing as _tp

import PyQt5.QtCore as _qtc

SideNr = _tp.Literal[0, 1, 2, 3]


class SideNrs:
    _ARGS = _tp.get_args(SideNr)

    LEFT = _ARGS[0]
    BOTTOM = _ARGS[1]
    RIGHT = _ARGS[2]
    TOP = _ARGS[3]


def getSideNr(portItemRect: _qtc.QRect, blockItemRect: _qtc.QRect) -> SideNr:
    portItemLeft, portItemRight, portItemTop, portItemBottom = (
        _getLeftRightTopBottom(portItemRect)
    )
    blockItemLeft, blockItemRight, blockItemTop, blockItemBottom = (
        _getLeftRightTopBottom(blockItemRect)
    )

    if portItemLeft <= blockItemLeft:
        return SideNrs.LEFT

    if portItemRight >= blockItemRight:
        return SideNrs.RIGHT

    if portItemTop <= blockItemTop:
        return SideNrs.TOP

    if portItemBottom >= blockItemBottom:
        return SideNrs.BOTTOM

    raise AssertionError("Port is inside block item.")


def _getLeftRightTopBottom(rect: _qtc.QRect) -> _tp.Tuple[int, int, int, int]:
    left = rect.x()
    right = rect.x() + rect.width()
    top = rect.y()
    bottom = rect.y() + rect.height()
    return left, right, top, bottom
