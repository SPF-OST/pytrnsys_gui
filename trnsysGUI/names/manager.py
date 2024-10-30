import abc as _abc
import pathlib as _pl
import typing as _tp

import pytrnsys.utils.result as _res


class AbstractDdckDirFileOrDirNamesProvider(_abc.ABC):
    @_abc.abstractmethod
    def hasFileOrDirName(self, name: str) -> bool:
        raise NotImplementedError()


class DdckDirFileOrDirNamesProvider(AbstractDdckDirFileOrDirNamesProvider):
    def __init__(self, ddckDirPath: _pl.Path):
        if not ddckDirPath.is_dir():
            raise ValueError("Not a directory.", ddckDirPath)

        self._ddckDirPath = ddckDirPath

    @_tp.override
    def hasFileOrDirName(self, name: str) -> bool:
        childNamesInLowerCase = [
            c.name.lower() for c in self._ddckDirPath.iterdir()
        ]
        nameInLowerCase = name.lower()

        hasFileOrDirName = nameInLowerCase in childNamesInLowerCase

        return hasFileOrDirName


class NamesManager:
    def __init__(
        self,
        existingNames: _tp.Sequence[str],
        ddckDirFileOrDirNamesProvider: AbstractDdckDirFileOrDirNamesProvider,
    ) -> None:
        self._existingNamesInLowerCase = {n.lower() for n in existingNames}
        self._ddckDirFileOrDirNamesProvider = ddckDirFileOrDirNamesProvider

    def validateName(
        self, newName: str, checkDdckFolder: bool
    ) -> _res.Result[None]:
        if newName == "":
            return _res.Error("Please enter a name.")

        if self._doesNameContainUnacceptableCharacters(newName):
            errorMessage = (
                "Found unacceptable characters (this includes spaces at the start and the end)\n"
                "Please use only letters, numbers, and underscores."
            )
            return _res.Error(errorMessage)

        if self._doesNameExist(newName):
            return _res.Error(
                "Name already exist (note: names are case insensitive)."
            )

        if (
            checkDdckFolder
            and self._ddckDirFileOrDirNamesProvider.hasFileOrDirName(newName)
        ):
            message = (
                f'There exists a file or folder named "{newName}" in the ddck folder. '
                f'Please delete it first before using "{newName}" as a name.'
            )
            return _res.Error(message)

        return None

    def addName(self, name: str) -> None:
        if self._doesNameExist(name):
            raise ValueError(f'Name already exists: "{name}".')

        nameInLowerCase = name.lower()
        self._existingNamesInLowerCase.add(nameInLowerCase)

    def removeName(self, name: str) -> None:
        if not self._doesNameExist(name):
            raise ValueError(f'Name does not exist: "{name}".')

        nameInLowerCase = name.lower()
        self._existingNamesInLowerCase.remove(nameInLowerCase)

    def _doesNameExist(self, newName: str) -> bool:
        newNameInLowerCase = newName.lower()
        doesNameExist = newNameInLowerCase in self._existingNamesInLowerCase
        return doesNameExist

    def _doesNameContainUnacceptableCharacters(self, name: str) -> bool:
        nameWithoutUnderscores = self._removeUnderscores(name)

        if self._doesContainOnlyNumbers(nameWithoutUnderscores):
            return True

        return not self._doesContainOnlyLettersAndNumbers(
            nameWithoutUnderscores
        )

    @staticmethod
    def _removeUnderscores(name: str) -> str:
        nameWithoutUnderscores = "".join(c for c in name if c != "_")
        return nameWithoutUnderscores

    @staticmethod
    def _doesContainOnlyLettersAndNumbers(string: str) -> bool:
        return string.isalnum()

    @staticmethod
    def _doesContainOnlyNumbers(string: str) -> bool:
        return string.isdigit()
