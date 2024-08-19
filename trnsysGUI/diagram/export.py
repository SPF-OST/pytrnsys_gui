from PyQt5 import QtCore as _qtc
from PyQt5 import QtGui as _qtg
from PyQt5 import QtPrintSupport as _qtp
from PyQt5 import QtSvg as _qsvg
from PyQt5 import QtWidgets as _qtw


def export(diagramScene: _qtw.QGraphicsScene, fileName: str) -> None:
    boundingRect = diagramScene.itemsBoundingRect()
    paintDevice = _getPaintDevice(fileName, boundingRect)

    painter = _qtg.QPainter()

    painter.begin(paintDevice)
    diagramScene.render(painter)
    painter.end()


def _getPaintDevice(fileName: str, boundingRect: _qtc.QRectF) -> _qtg.QPaintDevice:
    extension = getExtension(fileName)

    if extension == "pdf":
        printer = _qtp.QPrinter(_qtp.QPrinter.HighResolution)
        printer.setOrientation(_qtp.QPrinter.Landscape)
        printer.setOutputFormat(_qtp.QPrinter.PdfFormat)
        printer.setOutputFileName(fileName)
        return printer

    if extension == "svg":
        generator = _qsvg.QSvgGenerator()
        generator.setFileName(fileName)

        size = boundingRect.size()
        generator.setSize(size.toSize())

        viewBox = _qtc.QRectF(0.0, 0.0, size.width(), size.height())
        generator.setViewBox(viewBox)

        return generator

    raise ValueError("Invalid extension.", fileName)


def getExtension(fileName: str) -> str:
    suffix = _qtc.QFileInfo(fileName).suffix()
    return suffix
