from trnsysGUI.messageBox import MessageBox


class TestMessageBox:
    def testCreate(self, qtbot):
        """ This now works. """
        print("I am before message box")

        from PyQt5 import QtWidgets as _qtw
        qtbot.addWidget(_qtw.QMessageBox())
        print("I am after message box")
        assert False

    def testCreatePyQt6(self, qtbot):
        """ This reproduces the failure. """
        print("I am before message box")

        from PyQt6 import QtWidgets as _qtw

        qtbot.addWidget(_qtw.QMessageBox().exec())
        print("I am after message box")
        assert False

    def testCreate_actual(self, qtbot):
        from PyQt6.QtWidgets import QApplication
        app = QApplication([])
        qtbot.addWidget(MessageBox().create())
        assert False


def get_message_box(manual=False):
    from PyQt6.QtWidgets import QApplication, QMessageBox

    app = QApplication([])
    mbox = QMessageBox()
    if manual:
        mbox.exec()

    return mbox, app


def testCreatePyQt6_app(qtbot):
    """ This is able to open the message box in PyQt6.
        I have not been able to get this to work with qtbot yet.
    """
    manual = False  # set to true to try it out.
    mbox, app = get_message_box(manual)


