# pylint: skip-file
# type: ignore

__all__ = ["ImageAccessor"]

import pkgutil as _pu
import logging as _log
import typing as _tp
import abc as _abc
import pathlib as _pl

import PyQt5.QtGui as _qtg
import PyQt5.QtSvg as _qsvg
import PyQt5.QtCore as _qtc

import trnsysGUI

_logger = _log.getLogger("root")


class _DataLoaderBase(_abc.ABC):
    def __init__(self, logger: _log.Logger):
        self._logger = logger

    def loadData(self) -> bytes:
        try:
            data = self._loadDataImpl()
            if not data:
                raise AssertionError("Image data is empty.")
        except Exception as e:
            self._logger.exception(
                "An exception occurred loading image data for '%s'.",
                self.getResourcePath(),
                exc_info=True,
                stack_info=True,
            )
            raise e
        return data

    @_abc.abstractmethod
    def getResourcePath(self) -> str:
        pass

    @_abc.abstractmethod
    def getExtension(self) -> _tp.Optional[str]:
        pass

    @_abc.abstractmethod
    def _loadDataImpl(self) -> bytes:
        pass


class _PackageResourceDataLoader(_DataLoaderBase):
    PATH_PREFIX = "pkg_resource:"

    def __init__(self, packagePath: str, logger: _log.Logger):
        super().__init__(logger)

        self._resourcePath = packagePath

    def getResourcePath(self) -> str:
        return f"{self.PATH_PREFIX}{self._resourcePath}"

    def getExtension(self) -> _tp.Optional[str]:
        parts = self._resourcePath.split(".")

        extension = parts[-1] if parts else None

        return extension

    def _loadDataImpl(self) -> bytes:
        data = _pu.get_data(trnsysGUI.__name__, self._resourcePath)
        return data


class _FileDataLoader(_DataLoaderBase):
    PATH_PREFIX = "file:"

    def __init__(self, filePath: _pl.Path, logger: _log.Logger):
        super().__init__(logger)

        self._absoluteFilePath = filePath.absolute()

    def getResourcePath(self) -> str:
        return f"{self.PATH_PREFIX}{self._absoluteFilePath}"

    def getExtension(self) -> _tp.Optional[str]:
        extension = self._absoluteFilePath.suffix
        if not extension:
            return None

        return extension

    def _loadDataImpl(self) -> bytes:
        return self._absoluteFilePath.read_bytes()


class ImageAccessor:
    def __init__(self, dataLoader: _DataLoaderBase) -> None:
        self._dataLoader = dataLoader

    @staticmethod
    def createForPackageResource(resourcePath: str, logger: _log.Logger = _logger):
        dataLoader = _PackageResourceDataLoader(resourcePath, logger)

        return ImageAccessor(dataLoader)

    @staticmethod
    def createForFile(filePath: _pl.Path, logger: _log.Logger = _logger):
        dataLoader = _FileDataLoader(filePath, logger)

        return ImageAccessor(dataLoader)

    @classmethod
    def createFromResourcePath(cls, resourcePath: str, logger: _log.Logger = _logger) -> "ImageAccessor":
        dataLoader = cls._createDataLoaderFromResourcePath(resourcePath, logger)

        return ImageAccessor(dataLoader)

    @staticmethod
    def _createDataLoaderFromResourcePath(resourcePath: str, logger: _log.Logger) -> _DataLoaderBase:
        if resourcePath.startswith(_PackageResourceDataLoader.PATH_PREFIX):
            path = resourcePath[len(_PackageResourceDataLoader.PATH_PREFIX):]
            return _PackageResourceDataLoader(path, logger)

        if resourcePath.startswith(_FileDataLoader.PATH_PREFIX):
            path = resourcePath[len(_FileDataLoader.PATH_PREFIX):]
            return _FileDataLoader(_pl.Path(path), logger)

        logger.warning("Found legacy resource path %s: assuming it's a package resource.", resourcePath)
        return _PackageResourceDataLoader(resourcePath, logger)

    def getResourcePath(self) -> str:
        return self._dataLoader.getResourcePath()

    def getFileExtension(self):
        return self._dataLoader.getExtension()

    def pixmap(self, *, width: _tp.Optional[int] = None, height: _tp.Optional[int] = None) -> _qtg.QPixmap:
        image = self.image(width=width, height=height)

        return _qtg.QPixmap(image)

    def icon(self) -> _qtg.QIcon:
        pixmap = self.pixmap()

        return _qtg.QIcon(pixmap)

    def image(self, *, width: _tp.Optional[int] = None, height: _tp.Optional[int] = None) -> _qtg.QImage:
        if self.getFileExtension() == "svg":
            return self._svgImage(width=width, height=height)

        imageBytes = self._loadBytes()
        image = _qtg.QImage.fromData(imageBytes)

        size = self._getSize(image.size(), width=width, height=height)
        scaledImage = image.scaled(size)

        return scaledImage

    def _svgImage(self, *, width: int, height: int) -> _qtg.QImage:
        imageBytes = self._loadBytes()
        svgRenderer = _qsvg.QSvgRenderer(imageBytes)

        defaultSize = svgRenderer.defaultSize()
        size = self._getSize(defaultSize, width=width, height=height)

        image = _qtg.QImage(size, _qtg.QImage.Format_ARGB32_Premultiplied)
        image.fill(_qtc.Qt.transparent)
        painter = _qtg.QPainter(image)
        svgRenderer.render(painter)

        return image

    @staticmethod
    def _getSize(defaultSize: _qtc.QSize, *, width: int, height: int) -> _qtc.QSize:
        width = width if width else defaultSize.width()
        height = height if height else defaultSize.height()

        return _qtc.QSize(width, height)

    def _loadBytes(self) -> bytes:
        return self._dataLoader.loadData()
