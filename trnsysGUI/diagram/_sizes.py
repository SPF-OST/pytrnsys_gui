__all__ = ["setRelativeSizes"]

import typing as _tp

from PyQt5 import QtCore as _qtc
import PyQt5.QtWidgets as _qtw


def setRelativeSizes(
    splitter: _qtw.QSplitter, widgets: _tp.Sequence[_qtw.QWidget], relativeSizes: _tp.Sequence[int]
) -> None:
    # See https://stackoverflow.com/a/59806093
    maxMinSize = max(_getSizeComponent(w.minimumSizeHint(), splitter.orientation()) for w in widgets)
    sizes = [maxMinSize * rs for rs in relativeSizes]
    splitter.setSizes(sizes)


def _getSizeComponent(size: _qtc.QSize, splitterOrientation: _qtc.Qt.Orientation) -> int:
    if splitterOrientation == _qtc.Qt.Orientation.Vertical:  # pylint: disable=no-member
        return size.width()

    if splitterOrientation == _qtc.Qt.Orientation.Horizontal:  # pylint: disable=no-member
        return size.height()

    raise ValueError(f"Unknown orientation: {splitterOrientation}")
