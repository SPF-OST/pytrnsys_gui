import typing as _tp

import PyQt5.QtWidgets as _qtw
import PyQt5.QtGui as _qtg
import PyQt5.QtCore as _qtc

from trnsysGUI.hydraulicLoops import common as _common

try:
    from . import _UI_dialog_generated as _uigen
except ImportError as importError:
    raise AssertionError(  # pylint: disable=duplicate-code  # 2
        "Could not find the generated Python code for a .ui or .qrc file. Please run the "
        "`dev-tools\\generateGuiClassesFromQtCreatorStudioUiFiles.py' script from your "
        "`pytrnsys_gui` directory."
    ) from importError

from trnsysGUI.hydraulicLoops import model as _model


class MergeLoopsDialog(_qtw.QDialog, _uigen.Ui_mergeLoopsDialog):
    def __init__(
        self,
        loop1: _model.HydraulicLoop,
        loop2: _model.HydraulicLoop,
        occupiedNames: _tp.Set[str],
        fluids: _tp.Sequence[_model.Fluid],
    ) -> None:
        super().__init__()
        self.setupUi(self)

        self._loop1 = loop1
        self._loop2 = loop2
        self._occupiedNames = occupiedNames
        self._fluids = fluids

        self.mergeSummary: _common.Cancellable[_common.MergedLoopSummary] = "cancelled"

        needsDifferingFluidsWarning = self._loop1.fluid != self._loop2.fluid
        self.differingFluidsWarningWidget.setVisible(needsDifferingFluidsWarning)
        self.differingFluidsWarningLabel.setVisible(needsDifferingFluidsWarning)

        self._configureNameComboBox()
        self._configureFluidComboBox()
        self._configureApplyButton()
        self._configureAbortButton()

        self.nameComboBox.setCurrentIndex(0)
        self.fluidComboBox.setCurrentIndex(0)

    def _configureApplyButton(self):
        def onApply() -> None:
            nameValue = self.nameComboBox.currentText()
            isUserDefined = (
                    self._loop1.name.isUserDefined
                    or self._loop2.name.isUserDefined
                    or nameValue not in [self._loop1.name and self._loop2.name]
            )
            name = _model.UserDefinedName(nameValue) if isUserDefined else _model.AutomaticallyGeneratedName(nameValue)

            fluid = self.fluidComboBox.currentData()

            self.mergeSummary = _common.MergedLoopSummary(name, fluid)

            self.close()

        self.applyButton.clicked.connect(onApply)

    def _configureAbortButton(self):
        def onAbort() -> None:
            self.mergeSummary = "cancelled"
            self.close()

        self.abortButton.clicked.connect(onAbort)

    def _configureNameComboBox(self) -> None:
        def onCurrentTextChanged(newName: str) -> None:
            self._setWarningsAndApplyEnabledForValues(newName, self.fluidComboBox.currentData())

        self.nameComboBox.currentTextChanged.connect(onCurrentTextChanged)

        self.nameComboBox.addItem("")
        self.nameComboBox.addItem(self._loop1.name.value)
        self.nameComboBox.addItem(self._loop2.name.value)

    def _configureFluidComboBox(self) -> None:
        def onCurrentIndexChanged(newIndex: int) -> None:
            name = self.nameComboBox.currentText()
            _fluid = self.fluidComboBox.itemData(newIndex) if newIndex >= 0 else None
            self._setWarningsAndApplyEnabledForValues(name, _fluid)

        self.fluidComboBox.currentIndexChanged.connect(onCurrentIndexChanged)

        fluid1 = self._loop1.fluid
        fluid2 = self._loop2.fluid
        areFluidsSame = fluid1 == fluid2
        if areFluidsSame:
            fluid = fluid1
            self._addLoopFluidItemToComboBox(fluid, [self._loop1.name.value, self._loop2.name.value])
        else:
            self.fluidComboBox.addItem("", None)
            self._addLoopFluidItemToComboBox(fluid1, [self._loop1.name.value])
            self._addLoopFluidItemToComboBox(fluid2, [self._loop2.name.value])

        otherFluids = {*self._fluids} - {self._loop1.fluid, self._loop2.fluid}
        sortedOtherFluids = sorted(otherFluids, key=lambda f: f.name)
        for fluid in sortedOtherFluids:
            self.fluidComboBox.addItem(fluid.name, fluid)

    def _setWarningsAndApplyEnabledForValues(self, name: str, fluid: _tp.Optional[_model.Fluid]) -> None:
        isNameTaken = name in self._occupiedNames
        isNameEmpty = not name
        if isNameEmpty:
            self.invalidNameWarningWidget.setToolTip("You must specify a name")
        elif isNameTaken:
            self.invalidNameWarningWidget.setToolTip("This name is already in use")

        isNameValid = not isNameEmpty and not isNameTaken
        self.invalidNameWarningWidget.setVisible(not isNameValid)

        isAFluidSelected = bool(fluid)
        self.applyButton.setEnabled(isAFluidSelected)
        self.noFluidSelectedWarningWidget.setVisible(not isAFluidSelected)

        isApplyEnabled = isNameValid and isAFluidSelected
        self.applyButton.setEnabled(isApplyEnabled)

    def _addLoopFluidItemToComboBox(self, fluid: _model.Fluid, loopNamesWithFluid: _tp.Sequence[str]) -> None:
        sortedNames = sorted(loopNamesWithFluid)
        text = f"{fluid.name} ({', '.join(sortedNames)})"
        self.fluidComboBox.addItem(text, fluid)
        boldFont = _qtg.QFont()
        boldFont.setBold(True)
        itemIndex = self.fluidComboBox.count() - 1
        self.fluidComboBox.setItemData(itemIndex, boldFont, _qtc.Qt.FontRole)

    @staticmethod
    def showDialogAndGetResult(
        loop1: _model.HydraulicLoop,
        loop2: _model.HydraulicLoop,
        occupiedNames: _tp.Set[str],
        fluids: _tp.Sequence[_model.Fluid],

    ) -> _common.Cancellable[_common.MergedLoopSummary]:
        dialog = MergeLoopsDialog(loop1, loop2, occupiedNames, fluids)
        dialog.exec()
        return dialog.mergeSummary
