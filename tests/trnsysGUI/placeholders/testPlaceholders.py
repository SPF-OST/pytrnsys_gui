import logging as _log
import pathlib as _pl

import trnsysGUI.BlockItem as _bi
import trnsysGUI.diagram.Editor as _de
import trnsysGUI.internalPiping as _ip
import trnsysGUI.menus.projectMenu.exportPlaceholders as _eph
import trnsysGUI.menus.projectMenu.placeholders as _ph

_DATA_DIR_ = _pl.Path(__file__).parent / "data"


class TestPlaceholders:
    def testPlaceholders(self, qtbot):
        actualDirPath = _DATA_DIR_ / "TRIHP_dualSource"
        expectedDirPath = _DATA_DIR_ / "expected"
        actualJsonFilePath = actualDirPath / "DdckPlaceHolderValues.json"
        expectedJsonFilePath = expectedDirPath / "DdckPlaceHolderValues.json"

        editor = self._createEditor(actualDirPath)
        qtbot.addWidget(editor)

        valueWithWarnings = _eph.encodeDdckPlaceHolderValuesToJson(
            editor.projectFolder, actualJsonFilePath, editor.trnsysObj, editor.hydraulicLoops
        )
        assert not valueWithWarnings.hasWarnings()

        actualJsonText = actualJsonFilePath.read_text()  # pylint: disable=bad-option-value,unspecified-encoding
        expectedJsonText = expectedJsonFilePath.read_text()  # pylint: disable=bad-option-value,unspecified-encoding

        assert actualJsonText == expectedJsonText

    def testPlaceholdersMissingDdckDirCreatesWarning(self, qtbot):
        # leaving this for now to show simultaneous working of both.
        actualDirPath = _DATA_DIR_ / "TRIHP_dualSource"

        editor = self._createEditor(actualDirPath)
        qtbot.addWidget(editor)

        blockItems = [
            o for o in editor.trnsysObj if isinstance(o, _ip.HasInternalPiping) and isinstance(o, _bi.BlockItem)
        ]

        ddckDirNames = [b.getDisplayName() for b in blockItems]
        ddckDirNames.remove("HP")

        valueWithWarnings = _ph.getPlaceholderValues(ddckDirNames, blockItems, editor.hydraulicLoops)

        actualWarning = valueWithWarnings.toWarningMessage()
        expectedWarning = """\
The following components didn't have a corresponding directory of the same name in the ddck folder:

HP

This can happen if you're using a "template" ddck under a different name as its containing directory
(i.e. "PROJECT$ path\\to\\your\\template.ddck as different_name") - in which case you can ignore this warning
for that particular component - or it could indicate a missing ddck file.
"""
        assert actualWarning == expectedWarning

    @staticmethod
    def _createEditor(projectFolderPath):  # pylint: disable=duplicate-code
        logger = _log.Logger("root")
        editor = _de.Editor(
            parent=None,
            projectFolder=str(projectFolderPath),
            jsonPath=None,
            loadValue="load",
            logger=logger,
        )
        return editor
