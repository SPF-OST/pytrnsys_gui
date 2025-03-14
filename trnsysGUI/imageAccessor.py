import abc as _abc
import logging as _log
import pathlib as _pl
import pkgutil as _pu
import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtSvg as _qsvg

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
        except Exception as error:
            self._logger.exception(
                "An exception occurred loading image data for '%s'.",
                self.getResourcePath(),
                exc_info=True,
                stack_info=True,
            )
            raise error
        return data

    @_abc.abstractmethod
    def getResourcePath(self) -> str:
        pass

    @_abc.abstractmethod
    def getExtension(self) -> _tp.Optional[str]:
        pass

    @_abc.abstractmethod
    def _loadDataImpl(self) -> _tp.Optional[bytes]:
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

        if not parts:
            return None

        extension = f".{parts[-1]}"

        return extension

    def _loadDataImpl(self) -> _tp.Optional[bytes]:
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


class ImageAccessorBase(_abc.ABC):
    def __init__(self, dataLoader: _DataLoaderBase) -> None:
        self._dataLoader = dataLoader

    def getResourcePath(self) -> str:
        return self._dataLoader.getResourcePath()

    def getFileExtension(self):
        return self._dataLoader.getExtension()

    def pixmap(
        self,
        *,
        width: _tp.Optional[int] = None,
        height: _tp.Optional[int] = None,
    ) -> _qtg.QPixmap:
        image = self.image(width=width, height=height)
        return _qtg.QPixmap(image)

    def icon(self) -> _qtg.QIcon:
        pixmap = self.pixmap()
        return _qtg.QIcon(pixmap)

    @_abc.abstractmethod
    def image(
        self,
        *,
        width: _tp.Optional[int] = None,
        height: _tp.Optional[int] = None,
    ) -> _qtg.QImage:
        raise NotImplementedError()

    def _loadBytes(self) -> bytes:
        return self._dataLoader.loadData()

    @staticmethod
    def _getSize(
        defaultSize: _qtc.QSize,
        *,
        width: _tp.Optional[int],
        height: _tp.Optional[int],
    ) -> _qtc.QSize:
        width = width if width else defaultSize.width()
        height = height if height else defaultSize.height()

        return _qtc.QSize(width, height)


class PngImageAccessor(ImageAccessorBase):
    def __init__(self, dataLoader: _DataLoaderBase) -> None:
        if dataLoader.getExtension() != ".png":
            raise ValueError("Can only be used for PNGs.")

        super().__init__(dataLoader)

    def image(
        self,
        *,
        width: _tp.Optional[int] = None,
        height: _tp.Optional[int] = None,
    ) -> _qtg.QImage:
        imageBytes = self._loadBytes()
        image = _qtg.QImage.fromData(imageBytes)

        size = self._getSize(image.size(), width=width, height=height)
        scaledImage = image.scaled(size)

        return scaledImage


class SvgImageAccessor(ImageAccessorBase):
    def __init__(self, dataLoader: _DataLoaderBase) -> None:
        if dataLoader.getExtension() != ".svg":
            raise ValueError("Can only be used for SVGs.")

        super().__init__(dataLoader)

        self._renderer: _qsvg.QSvgRenderer | None = None

    def image(
        self,
        *,
        width: _tp.Optional[int] = None,
        height: _tp.Optional[int] = None,
    ) -> _qtg.QImage:
        defaultSize = self.renderer.defaultSize()
        size = self._getSize(defaultSize, width=width, height=height)

        image = _qtg.QImage(size, _qtg.QImage.Format_ARGB32_Premultiplied)
        image.fill(_qtc.Qt.transparent)

        painter = _qtg.QPainter(image)
        self.renderer.render(painter)

        return image

    @property
    def renderer(self) -> _qsvg.QSvgRenderer:
        if self._renderer:
            return self._renderer

        imageBytes = self._loadBytes()
        self._renderer = _qsvg.QSvgRenderer(imageBytes)

        return self._renderer


_T_co = _tp.TypeVar("_T_co", covariant=True, bound=ImageAccessorBase)


def createForPackageResource(
    clazz: _tp.Type[_T_co], resourcePath: str, logger: _log.Logger = _logger
) -> _T_co:
    dataLoader = _PackageResourceDataLoader(resourcePath, logger)
    return clazz(dataLoader)


def createForFile(
    filePath: _pl.Path, logger: _log.Logger = _logger
) -> ImageAccessorBase:
    dataLoader = _FileDataLoader(filePath, logger)
    imageAccessor = _createFromDataLoader(dataLoader)
    return imageAccessor


def createFromResourcePath(
    resourcePath: str, logger: _log.Logger = _logger
) -> ImageAccessorBase:
    dataLoader = _createDataLoaderFromResourcePath(resourcePath, logger)
    imageAccessor = _createFromDataLoader(dataLoader)
    return imageAccessor


def _createFromDataLoader(dataLoader: _DataLoaderBase) -> ImageAccessorBase:
    extension = dataLoader.getExtension()
    match extension:
        case ".png":
            return PngImageAccessor(dataLoader)
        case ".svg":
            return SvgImageAccessor(dataLoader)
        case _:
            raise ValueError("Unknown extension.", extension)


def _createDataLoaderFromResourcePath(
    resourcePath: str, logger: _log.Logger
) -> _DataLoaderBase:
    if resourcePath.startswith(_PackageResourceDataLoader.PATH_PREFIX):
        path = resourcePath[len(_PackageResourceDataLoader.PATH_PREFIX) :]
        return _PackageResourceDataLoader(path, logger)

    if resourcePath.startswith(_FileDataLoader.PATH_PREFIX):
        path = resourcePath[len(_FileDataLoader.PATH_PREFIX) :]
        return _FileDataLoader(_pl.Path(path), logger)

    logger.warning(
        "Found legacy resource path %s: assuming it's a package resource.",
        resourcePath,
    )
    return _PackageResourceDataLoader(resourcePath, logger)
