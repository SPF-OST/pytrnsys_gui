import PyQt5.QtCore as _qtc

import typing as _tp


SideNr = _tp.Literal[0, 1, 2, 3]


class SideNrs:
    _ARGS = _tp.get_args(SideNr)

    LEFT = _ARGS[0]
    BOTTOM = _ARGS[1]
    RIGHT = _ARGS[2]
    TOP = _ARGS[3]


def getSideNr(portItemRect: _qtc.QRect, blockItemRect: _qtc.QRect) -> SideNr:
    portItemLeft, portItemRight, portItemTop, portItemBottom = _getLeftRightTopBottom(portItemRect)
    blockItemLeft, blockItemRight, blockItemTop, blockItemBottom = _getLeftRightTopBottom(blockItemRect)

    if portItemLeft <= blockItemLeft:
        return SideNrs.LEFT
    elif portItemRight >= blockItemRight:
        return SideNrs.RIGHT
    elif portItemTop <= blockItemTop:
        return SideNrs.TOP
    elif portItemBottom >= blockItemBottom:
        return SideNrs.BOTTOM
    else:
        raise AssertionError("Port is inside block item.")


def _getLeftRightTopBottom(rect: _qtc.QRect) -> _tp.Tuple[int, int, int, int]:
    left = rect.x()
    right = rect.x() + rect.width()
    top = rect.y()
    bottom = rect.y() + rect.height()
    return left, right, top, bottom
