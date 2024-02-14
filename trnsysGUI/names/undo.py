import enum as _enum

import pytrnsys.utils.result as _res

import trnsysGUI.idGenerator as _idgen
import trnsysGUI.names.manager as _nm
import trnsysGUI.errors as _errors


class DeleteCommandTargetType(_enum.Enum):
    COMPONENT = "component"
    CONNECTION = "connection"


class UndoNamingHelper:
    def __init__(self, namesManager: _nm.NamesManager, idGenerator: _idgen.IdGenerator) -> None:
        self._namesManager = namesManager
        self._idGenerator = idGenerator

    def getOrCreateAndAddNonCollidingNameForAdd(
        self, oldName: str, targetType: DeleteCommandTargetType, checkDdckFolder: bool, generatedNamePrefix: str
    ) -> str:
        result = self._namesManager.validateName(oldName, checkDdckFolder)
        if not _res.isError(result):
            return oldName

        generatedName = self._createAndAddName(generatedNamePrefix, checkDdckFolder)
        errorMessage = (
            f'Could not use previous name "{oldName}" of {targetType.value} as it '
            f"has been used for other components or pipes in the meantime. The newly generated "
            f'name "{generatedName}" will be used instead. You might want to change it to a more '
            f"meaningful value manually."
        )
        _errors.showErrorMessageBox(errorMessage, title="Name changed")

        return generatedName

    def removeNameForDelete(self, name: str) -> None:
        self._namesManager.removeName(name)

    def _createAndAddName(self, prefix: str, checkDdckFolder: bool) -> str:
        for _ in range(1000):
            newId = self._idGenerator.getID()
            newNameCandidate = f"{prefix}{newId}"
            result = self._namesManager.validateName(newNameCandidate, checkDdckFolder)
            if not _res.isError(result):
                self._namesManager.addName(newNameCandidate)
                return newNameCandidate

        raise AssertionError(f'Could not generate a name with prefix "{prefix}".')
