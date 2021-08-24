import itertools as _it


class IdGenerator:  # pylint: disable=too-many-instance-attributes
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
        self.idCounter = _it.count(1)
        self.trnsysIdCounter = _it.count(1)
        self.connIdCounter = _it.count(1)
        self.storagenTesCounter = _it.count(1)
        self.storageTypeCounter = _it.count(1924)

    def getID(self):
        nextId = next(self.idCounter)
        self.ids.append(nextId)
        return nextId

    def getTrnsysID(self):
        nextId = next(self.trnsysIdCounter)
        self.trnsysIds.append(nextId)
        return nextId

    def getConnID(self):
        nextId = next(self.connIdCounter)
        self.connIds.append(nextId)
        return nextId

    def getStoragenTes(self):
        nextId = next(self.storagenTesCounter)
        self.storageTes.append(nextId)
        return nextId

    def getStorageType(self):
        nextId = next(self.storageTypeCounter)
        self.storageType.append(nextId)
        return nextId

    def setID(self, nextId):
        self.idCounter = _it.count(nextId)

    def setConnID(self, nextId):
        self.connIdCounter = _it.count(nextId)

    def setTrnsysID(self, nextId):
        self.trnsysIdCounter = _it.count(nextId)

    def reset(self):
        self.ids = []
        self.trnsysIds = []
        self.connIds = []
        self.storageTes = []
        self.storageType = []
        self.idCounter = _it.count(1)
        self.trnsysIdCounter = _it.count(1)
        self.connIdCounter = _it.count(1)
        self.storagenTesCounter = _it.count(1)
        self.storageTypeCounter = _it.count(1924)
