__all__ = [
    "assertThatGeneratedUIModuleAndResourcesExist",
    "assertThatLocalGeneratedUIModuleAndResourcesExist",
]

import importlib as _il

_ERROR_MESSAGE = (
    "Could not find the generated Python code for a .ui or .qrc file. Please run the "
    "`dev-tools\\generateGuiClassesFromQtCreatorStudioUiFiles.py' script from your "
    "`pytrnsys_gui` directory."
)

# This module needs to be imported at least once as it registers resources (icons, etc) with QT
# upon being imported. So even though it looks like an unused import DON'T REMOVE IT
try:
    import trnsysGUI.resources.QRC_resources_generated as _qresources
except ImportError as importError:
    raise AssertionError(_ERROR_MESSAGE) from importError

DEFAULT_MODULE_NAME = "_UI_dialog_generated"


def assertThatGeneratedUIModuleAndResourcesExist(
    packageName: str, *, moduleName: str = DEFAULT_MODULE_NAME
) -> None:
    try:
        _il.import_module(f".{moduleName}", packageName)
    except ImportError as importError:

        raise AssertionError(_ERROR_MESSAGE) from importError


def assertThatLocalGeneratedUIModuleAndResourcesExist(
    absoluteModuleName: str, *, moduleName: str = DEFAULT_MODULE_NAME
) -> None:
    """This functions assumes that the module to import is next to the calling module in the file hierarchy."""
    packageName = ".".join(absoluteModuleName.split(".")[:-1])
    assertThatGeneratedUIModuleAndResourcesExist(
        packageName, moduleName=moduleName
    )
