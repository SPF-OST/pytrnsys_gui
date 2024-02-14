import enum as _enum

import pytrnsys.utils.result as _res
import trnsysGUI.errors as _errors
import trnsysGUI.names.create as _nc
import trnsysGUI.names.manager as _nm


class DeleteCommandTargetType(_enum.Enum):
    COMPONENT = "component"
    CONNECTION = "connection"


class UndoNamingHelper:
    def __init__(self, namesManager: _nm.NamesManager, createNamingHelper: _nc.CreateNamingHelper) -> None:
        self._namesManager = namesManager
        self._createNamingHelper = createNamingHelper

    @staticmethod
    def create(namesManager: _nm.NamesManager) -> "UndoNamingHelper":
        createNamingHelper = _nc.CreateNamingHelper(namesManager)
        return UndoNamingHelper(namesManager, createNamingHelper)

    def addOrGenerateAndAddAnNonCollidingNameForAdd(
        self,
        oldName: str,
        targetType: DeleteCommandTargetType,
        checkDdckFolder: bool,
        generatedNameBase: str,
        firstGeneratedNameHasNumber: bool,
    ) -> str:
        result = self._namesManager.validateName(oldName, checkDdckFolder)
        if not _res.isError(result):
            self._namesManager.addName(oldName)
            return oldName

        generatedName = self._createNamingHelper.generateAndAdd(
            generatedNameBase, checkDdckFolder, firstGeneratedNameHasNumber
        )
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
