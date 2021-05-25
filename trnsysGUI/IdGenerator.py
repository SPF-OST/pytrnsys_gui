# pylint: skip-file
# type: ignore

import uuid
from itertools import count


class IdGenerator(object):
    def __init__(self):
        self.ids = []
        self.trnsysIds = []
        self.connIds = []
        self.blockIds = []
        self.storageTes = []
        self.storageType = []
        self.idCounter = count(1)
        self.trnsysIdCounter = count(1)
        self.connIdCounter = count(1)
        self.blockIdCounter = count(1)
        self.storagenTesCounter = count(1)
        self.storageTypeCounter = count(1924)

    def getUUID(self):
        x = uuid.uuid1().int
        self.uuids.append(x)
        return x

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

    def getBlockID(self):
        id = next(self.blockIdCounter)
        self.blockIds.append(id)
        return id

    def getStoragenTes(self):
        id = next(self.storagenTesCounter)
        self.storageTes.append(id)
        return id

    def getStorageType(self):
        id = next(self.storageTypeCounter)
        self.storageType.append(id)
        return id

    def setBlockID(self, id):
        self.blockIdCounter = count(id)

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
        self.blockIds = []
        self.storageTes = []
        self.storageType = []
        self.idCounter = count(1)
        self.trnsysIdCounter = count(1)
        self.connIdCounter = count(1)
        self.blockIdCounter = count(1)
        self.storagenTesCounter = count(1)
        self.storageTypeCounter = count(1924)
