import logging as log
import pathlib as pl
import shutil as sh

import PyQt5.QtWidgets as widgets

import trnsysGUI.diagram.Editor as de


class TestEditor:
    def testExportForMassFlowSolver(self):
        helper = _Helper()
        helper.setup()

        # The following line is required otherwise QT will crash
        _ = widgets.QApplication([])

        logger = log.Logger('root')
        editor = de.Editor(None, str(helper.projectFolderPath), jsonPath=None, loadValue='load', logger=logger)
        editor.exportData(exportTo='mfs')

        self._assertFileEquals(helper.actualDckFile, helper.expectedDckFile)

    @staticmethod
    def _assertFileEquals(actualFilePath, expectedFilePath):
        actualContent = actualFilePath.read_text()
        expectedContent = expectedFilePath.read_text()

        assert actualContent == expectedContent


class _Helper:
    def __init__(self):
        dataFolderPath = pl.Path(__file__).parent / 'data'

        self._actualFolderPath = dataFolderPath / 'actual'

        self.projectFolderPath = self._actualFolderPath / 'TRIHP_dualSource'
        expectedProjectFolderPath = dataFolderPath / 'expected' / 'TRIHP_dualSource'

        self.actualDckFile = self.projectFolderPath / 'TRIHP_dualSource_mfs.dck'
        self.expectedDckFile = expectedProjectFolderPath / 'TRIHP_dualSource_mfs.dck'

    def setup(self):
        self._copyExampleToTestInputFolder()

    def _copyExampleToTestInputFolder(self):
        if self._actualFolderPath.exists():
            sh.rmtree(self._actualFolderPath)

        pytrnsysGuiDir = pl.Path(__file__).parents[3]
        exampleFolderPath = pytrnsysGuiDir / 'trnsysGUI' / 'examples' / 'TRIHP_dualSource'

        sh.copytree(exampleFolderPath, self.projectFolderPath)

