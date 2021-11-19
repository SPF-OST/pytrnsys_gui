import typing as _tp
import dataclasses as _dc

import PyQt5.QtWidgets as _qtw

try:
    from . import _UI_mergeLoopsDialog_generated as _uigen
except ImportError as importError:
    raise AssertionError(  # pylint: disable=duplicate-code  # 2

        "Could not find the generated Python code for a .ui or .qrc file. Please run the "
        "`dev-tools\\generateGuiClassesFromQtCreatorStudioUiFiles.py' script from your "
        "`pytrnsys_gui` directory."
    ) from importError

from . import model as _model


@_dc.dataclass
class MergeResult:
    name: _model.Name
    fluid: _model.Fluid


class MergeLoopsDialog(_qtw.QDialog, _uigen.Ui_mergeLoopsDialog):
    def __init__(self, loop1: _model.HydraulicLoop, loop2: _model.HydraulicLoop):
        super().__init__()
        self.setupUi(self)

        self._loop1 = loop1
        self._loop2 = loop2

    @staticmethod
    def showDialogAndGetResult(
        loop1: _model.HydraulicLoop, loop2: _model.HydraulicLoop  # pylint: disable=unused-argument
    ) -> _tp.Union[_tp.Literal["cancelled"], MergeResult]:
        # TODO@damian.birchler
        return "cancelled"
