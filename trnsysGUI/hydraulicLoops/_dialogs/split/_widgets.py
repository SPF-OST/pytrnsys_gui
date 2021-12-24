import PyQt5.QtWidgets as _qtw
import PyQt5.QtCore as _qtc


class EnterLeaveNotifyingGroupBox(_qtw.QGroupBox):
    enter = _qtc.pyqtSignal()
    leave = _qtc.pyqtSignal()

    def enterEvent(self, _: _qtc.QEvent) -> None:
        self.enter.emit()

    def leaveEvent(self, _: _qtc.QEvent) -> None:
        self.leave.emit()
