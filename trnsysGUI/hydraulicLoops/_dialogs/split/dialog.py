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


class SplitLoopDialog(_qtw.QDialog, _uigen.Ui_splitHydraulicLoopDialog):
    @staticmethod
    def showDialogAndGetResult(
        loop: _model.HydraulicLoop,
        occupiedNames: _tp.Set[str],
        fluids: _tp.Sequence[_model.Fluid],
        setLoop1Selected: _tp.Callable[[bool], None],
        setLoop2Selected: _tp.Callable[[bool], None]
    ) -> _common.Cancellable[_common.SplitLoopsSummary]:
        dialog = SplitLoopDialog(loop, occupiedNames, fluids, setLoop1Selected, setLoop2Selected)
        dialog.exec()
        return dialog.splitSummary

    def __init__(
        self,
        loop: _model.HydraulicLoop,
        occupiedNames: _tp.Set[str],
        fluids: _tp.Sequence[_model.Fluid],
        setLoop1Selected: _tp.Callable[[bool], None],
        setLoop2Selected: _tp.Callable[[bool], None]
    ) -> None:
        super().__init__()
        self.setupUi(self)

        self._loop = loop
        self._occupiedNames = occupiedNames
        self._fluids = fluids
        self._setLoop1Selected = setLoop1Selected
        self._setLoop2Selected = setLoop2Selected

        self.splitSummary: _common.Cancellable[_common.SplitLoopsSummary] = "cancelled"

        self._configureGroupBoxes()

        self._configureNameComboBoxes()
        self.name1ComboBox.setCurrentIndex(0)
        self.name2ComboBox.setCurrentIndex(0)

        self._configureFluidComboBoxes()
        self.fluid1ComboBox.setCurrentIndex(0)
        self.fluid2ComboBox.setCurrentIndex(0)

        self._configureButtons()

        self._onAnyChange(self.name1ComboBox.currentText(), self.name2ComboBox.currentText())

    def _configureGroupBoxes(self) -> None:
        def onEnter1() -> None:
            self._setLoop1Selected(True)

        self.loop1GroupBox.enter.connect(onEnter1)

        def onLeave1() -> None:
            self._setLoop1Selected(False)

        self.loop1GroupBox.leave.connect(onLeave1)

        def onEnter2() -> None:
            self._setLoop2Selected(True)

        self.loop2GroupBox.enter.connect(onEnter2)

        def onLeave2() -> None:
            self._setLoop2Selected(False)

        self.loop2GroupBox.leave.connect(onLeave2)

    def _configureButtons(self) -> None:
        def deselectAllConnections() -> None:
            self._setLoop1Selected(False)
            self._setLoop2Selected(False)

        def onAbort() -> None:
            self.splitSummary = "cancelled"
            self.close()

        self.abortButton.clicked.connect(deselectAllConnections)
        self.abortButton.clicked.connect(onAbort)

        def onApply() -> None:
            name1Value = self._createNameForValue(self.name1ComboBox.currentText())
            name1 = name1Value
            name2Value = self.name2ComboBox.currentText()
            name2 = self._createNameForValue(name2Value)

            fluid1 = self.fluid1ComboBox.currentData()
            fluid2 = self.fluid2ComboBox.currentData()

            self.splitSummary = _common.SplitLoopsSummary(
                _common.LoopSummary(name1, fluid1), _common.LoopSummary(name2, fluid2)
            )

            self.close()

        self.applyButton.clicked.connect(deselectAllConnections)
        self.applyButton.clicked.connect(onApply)

    def _createNameForValue(self, nameValue: str) -> _model.Name:
        if nameValue != self._loop.name.value:
            return _model.UserDefinedName(nameValue)

        if self._loop.name.isUserDefined:
            return _model.UserDefinedName(nameValue)

        return _model.AutomaticallyGeneratedName(nameValue)

    def _configureFluidComboBoxes(self) -> None:
        self._configureFluidComboBox(self.fluid1ComboBox)
        self._configureFluidComboBox(self.fluid2ComboBox)

    def _configureFluidComboBox(self, fluidComboBox: _qtw.QComboBox) -> None:
        fluidComboBox.addItem(self._loop.fluid.name, self._loop.fluid)
        boldFont = _qtg.QFont()
        boldFont.setBold(True)
        fluidComboBox.setItemData(0, boldFont, _qtc.Qt.FontRole)
        otherFluids = {*self._fluids} - {self._loop.fluid}
        sortedOtherFluids = sorted(otherFluids, key=lambda f: f.name)
        for otherFluid in sortedOtherFluids:
            fluidComboBox.addItem(otherFluid.name, otherFluid)

    def _configureNameComboBoxes(self) -> None:
        self.name1ComboBox.addItem("")
        self.name1ComboBox.addItem(self._loop.name.value)

        def onName1TextChanged(newName: str) -> None:
            self._onAnyChange(
                newName,
                self.name2ComboBox.currentText(),
            )

        self.name1ComboBox.currentTextChanged.connect(onName1TextChanged)

        self.name2ComboBox.addItem("")
        self.name2ComboBox.addItem(self._loop.name.value)

        def onName2TextChanged(newName: str) -> None:
            self._onAnyChange(
                self.name1ComboBox.currentText(),
                newName,
            )

        self.name2ComboBox.currentTextChanged.connect(onName2TextChanged)

    def _onAnyChange(self, name1: str, name2: str) -> None:
        areNamesOk = self._onEitherNameChanged(name1, name2)
        self.applyButton.setEnabled(areNamesOk)

    def _onEitherNameChanged(self, name1: str, name2: str) -> bool:
        isName1Valid = self._onNameChanged(name1, self.name1WarningWidget)
        isName2Valid = self._onNameChanged(name2, self.name2WarningWidget)

        if not isName1Valid or not isName2Valid:
            return False

        if name1 == name2:
            tooltip = "The names of the two loops must differ"
            self.name1WarningWidget.setToolTip(tooltip)
            self.name1WarningWidget.setVisible(True)
            self.name2WarningWidget.setToolTip(tooltip)
            self.name2WarningWidget.setVisible(True)

            return False

        return True

    def _onNameChanged(self, newName: str, warningWidget: _qtw.QWidget) -> bool:
        isEmpty = not newName
        isInUse = newName in self._occupiedNames
        tooltip = ""
        if isEmpty:
            tooltip = "You must specify a name"
        elif isInUse:
            tooltip = "This name is already in use"

        isValid = not isEmpty and not isInUse

        warningWidget.setVisible(not isValid)
        warningWidget.setToolTip(tooltip)

        return isValid
