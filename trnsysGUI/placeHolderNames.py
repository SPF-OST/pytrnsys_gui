def getQualifiedPortName(nodeName: str | None, portName: str) -> str:
    nodeNameOrEmpty = nodeName or ""
    nodeNamePart = nodeNameOrEmpty.capitalize()

    portNamePart = portName.capitalize()

    qualifiedPortName = f"{nodeNamePart}{portNamePart}"

    return qualifiedPortName
