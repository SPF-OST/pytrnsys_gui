import pytrnsys.utils.result as _res


class ComponentAndPipeNameValidator:

    def __init__(self, existingNames):
        self._existingNamesInLowerCase = [n.lower() for n in existingNames]

    def validateName(self, newName: str) -> _res.Result[None]:
        if newName == "":
            return _res.Error("Please enter a name.")

        if self._doesNameContainUnacceptableCharacters(newName):
            errorMessage = "Found unacceptable characters (this includes spaces at the start and the end)\n" \
                           "Please use only letters, numbers, and underscores."
            return _res.Error(errorMessage)

        if self._doesNameExist(newName):
            return _res.Error("Name already exist (note: names are case insensitive).")

        return None

    def _doesNameExist(self, newName: str) -> bool:
        newNameInLowerCase = newName.lower()
        doesNameExist = newNameInLowerCase in self._existingNamesInLowerCase
        return doesNameExist

    def _doesNameContainUnacceptableCharacters(self, name: str) -> bool:
        nameWithoutUnderscores = self._removeUnderscores(name)

        if self._doesContainOnlyNumbers(nameWithoutUnderscores):
            return True

        return not self._doesContainOnlyLettersAndNumbers(nameWithoutUnderscores)

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
