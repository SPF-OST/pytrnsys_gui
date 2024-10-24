class TestMessageBox:
    def testCreate(self):
        print("I am before message box")

        from PyQt6 import QtWidgets as _qtw

        msgBox = _qtw.QMessageBox()
        print("I am after message box")
        assert False
