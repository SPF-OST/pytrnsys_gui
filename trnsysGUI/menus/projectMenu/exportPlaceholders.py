import json as _json
import pathlib as _pl
import typing as _tp

import PyQt5.QtWidgets as _qtw

import pytrnsys.utils.result as _res
import pytrnsys.utils.warnings as _warn
import trnsysGUI.blockItemHasInternalPiping as _biip
import trnsysGUI.diagram.Editor as _ed
import trnsysGUI.hydraulicLoops.model as _hlm
import trnsysGUI.internalPiping as _ip
import trnsysGUI.menus.projectMenu.placeholders as _ph
import trnsysGUI.warningsAndErrors as _werrs


def exportDdckPlaceHolderValuesJsonFile(editor: _ed.Editor) -> _res.Result[None]:  # type: ignore[name-defined]
    if not editor.isHydraulicConnected():
        return _res.Error("You need to connect all port items before you can export the hydraulics.")

    jsonFilePath = _pl.Path(editor.projectFolder) / "DdckPlaceHolderValues.json"

    if jsonFilePath.is_dir():
        _qtw.QMessageBox.information(
            editor,
            "Folder already exists",
            f"A folder already exits at f{jsonFilePath}. Chose a different location or delete the folder first.",
        )
        return None

    if jsonFilePath.is_file():
        pressedButton = _qtw.QMessageBox.question(
            editor,
            "Overwrite file?",
            f"The file {jsonFilePath} already exists. Do you want to overwrite it or cancel?",
            buttons=(_qtw.QMessageBox.Save | _qtw.QMessageBox.Cancel),
            defaultButton=_qtw.QMessageBox.Cancel,
        )

        if pressedButton != _qtw.QMessageBox.Save:
            return None

    valueWithWarnings = encodeDdckPlaceHolderValuesToJson(
        editor.projectFolder, jsonFilePath, editor.trnsysObj, editor.hydraulicLoops
    )
    if valueWithWarnings.hasWarnings():
        message = (
            "The following warnings were generated while creating the ddck placeholder file:\n\n"
            + valueWithWarnings.toWarningMessage()
            + "\n"
        )
        _werrs.showMessageBox(message, title="Warnings encountered generating placeholders")

    _qtw.QMessageBox.information(
        editor,
        "Saved successfully",
        f"Saved place holder values JSON file at {jsonFilePath}.",
        buttons=_qtw.QMessageBox.Ok,
    )

    return None


def encodeDdckPlaceHolderValuesToJson(
    projectFolder: _pl.Path,
    filePath: _pl.Path,
    trnsysObjects: _tp.Sequence[_ip.HasInternalPiping],
    hydraulicLoops: _hlm.HydraulicLoops,
) -> _warn.ValueWithWarnings[None]:

    ddckDirNames = _getDdckDirNames(projectFolder)

    blockItems = [o for o in trnsysObjects if isinstance(o, _biip.BlockItemHasInternalPiping)]

    placeHoldersWithWarnings = _ph.getPlaceholderValues(ddckDirNames, blockItems, hydraulicLoops)

    ddckPlaceHolderValuesDictionary = placeHoldersWithWarnings.value

    jsonContent = _json.dumps(ddckPlaceHolderValuesDictionary, indent=4, sort_keys=True)
    filePath.write_text(jsonContent)

    return placeHoldersWithWarnings.withValue(None)


def _getDdckDirNames(projectFolder) -> _tp.Sequence[str]:
    ddckDirPath = _pl.Path(projectFolder) / "ddck"

    componentDdckDirPaths = list(ddckDirPath.iterdir())

    ddckDirNames = []
    for componentDirPath in componentDdckDirPaths:
        ddckDirNames.append(componentDirPath.name)

    return ddckDirNames
