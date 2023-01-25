class CheckPipeName:
    def __init__(self, name, existingNames):
        self.response = None
        self.name = name
        self.existingNames = existingNames
        self.nameWithoutUnderscores = self.removeUnderscores()
        self.errorMessage = self.checkValidity()

    def nameContainsUnacceptableCharacters(self):
        if self.containsOnlyNumbers(self.nameWithoutUnderscores):
            return True
        return not self.containsOnlyLettersAndNumbers(self.nameWithoutUnderscores)

    def removeUnderscores(self):
        nameWithoutUnderscores = "".join(list(filter(None, self.name.split('_'))))
        return nameWithoutUnderscores

    @staticmethod
    def containsOnlyLettersAndNumbers(string1):
        return string1.isalnum()

    @staticmethod
    def containsOnlyNumbers(string1):
        return string1.isdigit()

    @staticmethod
    def nameExists(newName, existingNames):
        for name in existingNames:
            if name.lower() == newName.lower():
                return True
        return False

    def checkValidity(self):
        newName = self.name
        if newName == "":
            errorMessage = "Please Enter a name!"
            return errorMessage
        if self.nameContainsUnacceptableCharacters():
            errorMessage = "Found unacceptable characters (this includes spaces at the start and the end)\n" \
                           "Please use only letters, numbers, and underscores."
            return errorMessage
        if self.nameExists(newName, self.existingNames):
            errorMessage = "Name already exist!"
            return errorMessage
        return None
