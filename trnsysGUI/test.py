from cmath import sqrt


def getID():
    global globalID
    globalID += 1
    return globalID


def getConnID():
    global globalConnID
    globalConnID += 1
    return globalConnID


def getTrnsysID():
    global trnsysID
    trnsysID += 1
    return trnsysID


def getSegID():
    global globalSegID
    globalSegID += 1
    return globalSegID


def calcDist(p1, p2):
    vec = p1 - p2
    norm = sqrt(vec.x() ** 2 + vec.y() ** 2)
    return norm
