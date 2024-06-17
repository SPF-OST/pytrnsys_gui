COMPONENTS_BASE_RESOURCE_PATH = "components/plugin/data"


def getComponentResourcePath(typeName: str) -> str:
    return f"{COMPONENTS_BASE_RESOURCE_PATH}/{typeName}"
