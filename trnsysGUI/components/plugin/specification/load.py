import abc as _abc
import collections.abc as _cabc
import dataclasses as _dc
import pathlib as _pl
import pkgutil as _pu

import pydantic as _pc
import yaml as _yaml
import yaml.parser as _yp

import pytrnsys.utils.result as _res
import trnsysGUI as _trnsysGui

from . import model as _model
from .. import _paths


@_dc.dataclass
class ResourceLoaderBase(_abc.ABC):
    @_abc.abstractmethod
    def loadBytes(self, resourcePath: str) -> bytes:
        raise NotImplementedError()


class FileResourceLoader(ResourceLoaderBase):
    def loadBytes(self, resourcePath: str) -> bytes:
        path = _pl.Path(resourcePath)
        return path.read_bytes()


class PackageResourceLoader(ResourceLoaderBase):
    def loadBytes(self, resourcePath: str) -> bytes:
        return _pu.get_data(_trnsysGui.__name__, resourcePath)


PACKAGE_RESOURCE_LOADER = PackageResourceLoader()


@_dc.dataclass
class Loader:
    baseResourcePath: str
    resourceLoader: ResourceLoaderBase

    @staticmethod
    def createPackageResourceLoader():
        loader = Loader(_paths.COMPONENTS_BASE_RESOURCE_PATH, PACKAGE_RESOURCE_LOADER)
        return loader

    def load(self, typeName: str) -> _res.Result[_model.Specification]:
        pluginPath = f"{self.baseResourcePath}/{typeName}"

        specificationResult = self._loadSpecification(pluginPath)
        if _res.isError(specificationResult):
            return _res.error(specificationResult)
        specification = _res.value(specificationResult)

        return specification

    def _loadSpecification(self, pluginResourcePath: str) -> _res.Result[_model.Specification]:
        specResourcePath = f"{pluginResourcePath}/spec.yaml"
        bytesResult = self._loadData(specResourcePath)
        if _res.isError(bytesResult):
            return _res.error(bytesResult)
        bytes_ = _res.value(bytesResult)

        dataResult = self._loadYaml(bytes_)
        if _res.isError(dataResult):
            return _res.error(dataResult).withContext(f"Syntax error in `{specResourcePath}`")
        data = _res.value(dataResult)

        specificationResult = self._createSpecification(data)
        if _res.isError(specificationResult):
            return _res.error(specificationResult).withContext(f"Error in specification `{specResourcePath}`")
        specification = _res.value(specificationResult)

        return specification

    def _loadData(self, resourcePath: str) -> _res.Result[bytes]:
        try:
            return self.resourceLoader.loadBytes(resourcePath)
        except FileNotFoundError:
            return _res.Error(f"`{resourcePath}` could not be found.")
        except PermissionError:
            return _res.Error(f"`{resourcePath}` could not be read. Maybe it's a directory instead of a file?")

    @staticmethod
    def _loadYaml(bytes_: bytes) -> _res.Result[_cabc.Mapping]:
        try:
            return _yaml.safe_load(bytes_)
        except _yp.ParserError as parseError:
            return _res.Error(str(parseError))

    @staticmethod
    def _createSpecification(data: _cabc.Mapping) -> _res.Result[_model.Specification]:
        try:
            return _model.Specification(**data)
        except _pc.ValidationError as validationError:
            return _res.Error(str(validationError))
