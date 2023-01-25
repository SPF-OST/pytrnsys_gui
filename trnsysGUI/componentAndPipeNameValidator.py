import typing as _tp


class ComponentAndPipeNameValidator:

    def __init__(self, existingNames):
        self._existingNamesInLowerCase = [n.lower() for n in existingNames]

    def validateName(self, newName: str) -> _tp.Optional[str]:
        if newName == "":
            return "Please enter a name."

        if self._nameContainsUnacceptableCharacters(newName):
            errorMessage = "Found unacceptable characters (this includes spaces at the start and the end)\n" \
                           "Please use only letters, numbers, and underscores."
            return errorMessage

        if self._nameExists(newName):
            return "Name already exist (note: names are case insensitive)."

        return None

    def _nameExists(self, newName: str) -> bool:
        newNameInLowerCase = newName.lower()
        doesNameExist = newNameInLowerCase in self._existingNamesInLowerCase
        return doesNameExist

    def _nameContainsUnacceptableCharacters(self, name: str) -> bool:
        nameWithoutUnderscores = self._removeUnderscores(name)

        if self._containsOnlyNumbers(nameWithoutUnderscores):
            return True

        return not self._containsOnlyLettersAndNumbers(nameWithoutUnderscores)

    @staticmethod
    def _removeUnderscores(name: str) -> str:
        nameWithoutUnderscores = "".join(c for c in name if c != "_")
        return nameWithoutUnderscores

    @staticmethod
    def _containsOnlyLettersAndNumbers(string: str) -> bool:
        return string.isalnum()

    @staticmethod
    def _containsOnlyNumbers(string: str) -> bool:
        return string.isdigit()
