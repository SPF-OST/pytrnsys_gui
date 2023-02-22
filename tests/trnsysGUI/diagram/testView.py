import logging as _log

import pytest as _pt
import trnsysGUI.diagram.Editor as _de
from trnsysGUI.Graphicaltem import GraphicalItem


class TestView:
    def setup(self):
        self.editor = self._createEditor('.')

    def testGraphicalItemWithNone(self):
        with _pt.raises(SystemExit) as e:
            GraphicalItem(self.editor)

    @staticmethod
    def _createEditor(projectFolderPath):
        logger = _log.Logger("root")
        editor = _de.Editor(
            parent=None,
            projectFolder=str(projectFolderPath),
            jsonPath=None,
            loadValue="load",
            logger=logger,
        )
        return editor
