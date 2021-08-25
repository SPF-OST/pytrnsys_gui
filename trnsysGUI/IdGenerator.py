# pylint: skip-file
# type: ignore

from itertools import count


class IdGenerator(object):
    # This value is used for the IDs when migrating from old JSON formats.
    # After deserialization the IDs are set such that there are no duplicate
    # IDs across all objects.
    UNINITIALIZED_ID = -1

    def __init__(self):
        self.ids = []
        self.trnsysIds = []
        self.connIds = []
        self.storageTes = []
        self.storageType = []
        self.idCounter = count(1)
        self.trnsysIdCounter = count(1)
        self.connIdCounter = count(1)
        self.storagenTesCounter = count(1)
        self.storageTypeCounter = count(1924)

    def getID(self):
        id = next(self.idCounter)
        self.ids.append(id)
        return id

    def getTrnsysID(self):
        id = next(self.trnsysIdCounter)
        self.trnsysIds.append(id)
        return id

    def getConnID(self):
        id = next(self.connIdCounter)
        self.connIds.append(id)
        return id

    def getStoragenTes(self):
        id = next(self.storagenTesCounter)
        self.storageTes.append(id)
        return id

    def getStorageType(self):
        id = next(self.storageTypeCounter)
        self.storageType.append(id)
        return id

    def setID(self, id):
        self.idCounter = count(id)

    def setConnID(self, id):
        self.connIdCounter = count(id)

    def setTrnsysID(self, id):
        self.trnsysIdCounter = count(id)

    def reset(self):
        self.ids = []
        self.trnsysIds = []
        self.connIds = []
        self.storageTes = []
        self.storageType = []
        self.idCounter = count(1)
        self.trnsysIdCounter = count(1)
        self.connIdCounter = count(1)
        self.storagenTesCounter = count(1)
        self.storageTypeCounter = count(1924)
