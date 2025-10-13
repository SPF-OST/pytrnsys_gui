import typing as _tp

import pytrnsys.utils.result as _res

import trnsysGUI.names.manager as _nm


class RenameHelper:
    def __init__(self, namesManager: _nm.NamesManager) -> None:
        self._namesManager = namesManager

    def canRename(
        self,
        currentName: _tp.Optional[str],
        newName: str,
        checkDdckFolder: bool,
    ) -> _res.Result[None]:
        if currentName:
            isNameUnchangedExceptForCasing = self.isSameName(
                currentName, newName
            )
            if isNameUnchangedExceptForCasing:
                return None

        return self._namesManager.validateName(newName, checkDdckFolder)

    @staticmethod
    def isSameName(currentName, newName):
        isNameUnchangedExceptForCasing = newName.lower() == currentName.lower()
        return isNameUnchangedExceptForCasing

    def rename(self, oldName: str, newName: str) -> None:
        self._namesManager.removeName(oldName)
        self._namesManager.addName(newName)
