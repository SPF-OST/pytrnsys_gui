import pytrnsys.utils.result as _res

import trnsysGUI.names.manager as _nm


class CreateNamingHelper:
    _N_MAX_TRIES = 1000

    def __init__(self, namesManager: _nm.NamesManager) -> None:
        self._namesManager = namesManager

    def generateAndAdd(
        self,
        baseName: str,
        checkDdckFolder: bool,
        firstGeneratedNameHasNumber: bool,
    ) -> str:
        for i in range(1, self._N_MAX_TRIES + 1):
            if i == 1 and not firstGeneratedNameHasNumber:
                newNameCandidate = baseName
            else:
                newNameCandidate = f"{baseName}{i}"

            result = self._namesManager.validateName(newNameCandidate, checkDdckFolder)
            if not _res.isError(result):
                self._namesManager.addName(newNameCandidate)
                return newNameCandidate

        raise AssertionError(f'Could not generate a name with base "{baseName}" after {self._N_MAX_TRIES} tries.')
