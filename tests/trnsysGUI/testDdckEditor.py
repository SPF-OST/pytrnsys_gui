# pylint: disable=invalid-name  # `tmp_path` fixture
# pylint: disable=protected-access
import pathlib as _pl

import pytest as _pt
import PyQt5.QtWidgets as _qtw

import trnsysGUI.ddckEditor.placeholders as _ph
import trnsysGUI.ddckEditor.tab as _tab
import trnsysGUI.ddckEditor.validation as _val

_VALUES_BY_PORT = {
    "In": {"@temp": "TPiColIn", "@mfr": "MCollector_A"},
    "Out": {"@temp": "TCollector"},
}

_VALID_DDCK = """\
*************************************
** A comment with @temp(Nope) in it
*************************************
EQUATIONS 2
TIn = @temp(In) ! inlet
MfrIn = @mfr(In)
EQUATIONS 1
@temp(Out) = TIn + 1
"""


class TestPlaceholders:
    def testFindPlaceholders(self):
        matches = _ph.findPlaceholders(
            "a = @temp(In) + @mfr( Out , MDef) * @energy(in, heat, Coll)"
        )

        assert [m.text for m in matches] == [
            "@temp(In)",
            "@mfr( Out , MDef)",
            "@energy(in, heat, Coll)",
        ]
        assert matches[1].portProperty == "@mfr"
        assert matches[1].portName == "Out"
        assert matches[1].defaultVariableName == "MDef"
        assert not matches[2].isHydraulic

    def testResolve(self):
        (match,) = _ph.findPlaceholders("@temp(In)")

        assert _ph.resolve(match, _VALUES_BY_PORT) == "TPiColIn"
        assert _ph.resolve(match, None) is None

    def testUnresolvedOnlyIfDiagramKnownAndNoDefault(self):
        missing, withDefault = _ph.findPlaceholders(
            "@rho(In) @rho(In, RhoDefault)"
        )

        assert _ph.isUnresolved(missing, _VALUES_BY_PORT)
        assert not _ph.isUnresolved(withDefault, _VALUES_BY_PORT)
        assert not _ph.isUnresolved(missing, None)

    def testFindPlaceholderAt(self):
        line = "x = @temp(In)"

        assert _ph.findPlaceholderAt(line, 2) is None
        assert _ph.findPlaceholderAt(line, 4).text == "@temp(In)"
        assert _ph.findPlaceholderAt(line, 12).text == "@temp(In)"
        assert _ph.findPlaceholderAt(line, 13) is None


class TestValidation:
    def testValidDdck(self):
        assert not _val.validateDdck(_VALID_DDCK, "Coll", _VALUES_BY_PORT)

    def testWrongNumberOfEquations(self):
        content = _VALID_DDCK.replace("EQUATIONS 2", "EQUATIONS 3")

        (problem,) = _val.validateDdck(content, "Coll", _VALUES_BY_PORT)

        assert problem.lineNumber == 4
        assert "declared number of equations (3)" in problem.message

    def testSyntaxError(self):
        content = _VALID_DDCK.replace("MfrIn = @mfr(In)", "MfrIn = = 1")

        (problem,) = _val.validateDdck(content, "Coll", _VALUES_BY_PORT)

        assert problem.lineNumber == 6

    def testUnresolvedPlaceholdersAreReportedWithLineNumbers(self):
        content = _VALID_DDCK.replace("@mfr(In)", "@mfr(Middle)")

        problems = _val.validateDdck(content, "Coll", _VALUES_BY_PORT)

        assert [p.lineNumber for p in problems] == [6]
        assert "Middle" in problems[0].message

    def testWithoutDiagramPlaceholdersNeedDefaults(self):
        withoutDefaults = _val.validateDdck(_VALID_DDCK, "Coll", None)
        withDefaults = _val.validateDdck(
            "EQUATIONS 1\nTIn = @temp(In, TDefault)\n", "Coll", None
        )

        assert withoutDefaults
        assert not withDefaults

    def testComponentNameIsContainingDirectory(self):
        path = _pl.Path("project/ddck/Collector/type1.ddck")

        assert _val.getComponentName(path) == "Collector"


class TestFileContent:
    def testWindows1252AndCrlfArePreserved(self, tmp_path):
        filePath = tmp_path / "file.ddck"
        originalBytes = "a = 1 ! 20 °C\r\nb = 2\r\n".encode("windows-1252")
        filePath.write_bytes(originalBytes)

        content = _tab._FileContent.read(
            filePath
        )  # pylint: disable=protected-access

        assert content.encoding == "windows-1252"
        assert content.newline == "\r\n"
        assert "\r" not in content.text
        assert content.toBytes() == originalBytes

    def testAsciiDeckFilesAreSavedAsWindows1252(self, tmp_path):
        filePath = tmp_path / "file.ddck"
        filePath.write_bytes(b"a = 1\n")

        content = _tab._FileContent.read(filePath)

        assert content.encoding == "windows-1252"

    def testUtf8AndLf(self, tmp_path):
        filePath = tmp_path / "file.json"
        filePath.write_bytes('{"a": "é"}\n'.encode("utf-8"))

        content = _tab._FileContent.read(
            filePath
        )  # pylint: disable=protected-access

        assert content.encoding == "utf-8"
        assert content.newline == "\n"


class TestIsTextFile:
    @_pt.mark.parametrize(
        "name", ["a.ddck", "b.DCK", "run.config", "c.json", "d.txt"]
    )
    def testTextFiles(self, name):
        assert _tab.isTextFile(_pl.Path(name))

    @_pt.mark.parametrize("name", ["a.prt", "b.png", "c.xlsx", "noSuffix"])
    def testOtherFiles(self, name):
        assert not _tab.isTextFile(_pl.Path(name))


@_pt.fixture(name="ddckFilePath")
def _ddckFilePath(tmp_path) -> _pl.Path:
    filePath = tmp_path / "ddck" / "Coll" / "coll.ddck"
    filePath.parent.mkdir(parents=True)
    filePath.write_bytes(_VALID_DDCK.replace("\n", "\r\n").encode("cp1252"))
    return filePath


@_pt.fixture(name="editorTab")
def _editorTab(qtbot) -> _tab.DdckEditorTab:
    editorTab = _tab.DdckEditorTab(lambda: {"Coll": _VALUES_BY_PORT})
    qtbot.addWidget(editorTab)
    return editorTab


# pylint: disable=protected-access
class TestDdckEditorTab:
    def testOpenEditAndSave(self, editorTab, ddckFilePath):
        assert editorTab.openFile(ddckFilePath)
        assert editorTab.openFile(ddckFilePath)  # opening twice: same tab
        assert editorTab._documentTabs.count() == 1

        document = editorTab._getCurrentDocument()
        assert not document.problems
        assert document.valuesByPort == _VALUES_BY_PORT

        document.editor.appendPlainText("CONSTANTS 1\nx = 1")
        assert editorTab.hasUnsavedChanges()
        assert editorTab._documentTabs.tabText(0) == "coll.ddck *"

        assert editorTab.saveDocument(document)

        assert not editorTab.hasUnsavedChanges()
        assert editorTab._documentTabs.tabText(0) == "coll.ddck"
        savedBytes = ddckFilePath.read_bytes()
        assert savedBytes.endswith(b"CONSTANTS 1\r\nx = 1")
        assert b"\r\r" not in savedBytes

    def testSaveValidates(self, editorTab, ddckFilePath):
        editorTab.openFile(ddckFilePath)
        document = editorTab._getCurrentDocument()

        document.editor.appendPlainText("EQUATIONS 1\ny = @cp(In)")
        editorTab.saveDocument(document)

        # 8 lines + empty last line + "EQUATIONS 1" -> line 11
        assert [p.lineNumber for p in document.problems] == [11]
        assert editorTab._problemsList.count() == 1

    def testExternalChangeReloadsUnmodifiedFile(self, editorTab, ddckFilePath):
        editorTab.openFile(ddckFilePath)
        document = editorTab._getCurrentDocument()

        ddckFilePath.write_text("CONSTANTS 1\nchanged = 1\n")
        editorTab._onFileChangedOnDisk(str(ddckFilePath))

        assert document.getText() == "CONSTANTS 1\nchanged = 1\n"
        assert not document.isModified

    def testUnsavedChangesAreKeptIfUserDeclinesReload(
        self, editorTab, ddckFilePath, monkeypatch
    ):
        editorTab.openFile(ddckFilePath)
        document = editorTab._getCurrentDocument()
        document.editor.appendPlainText("! mine")

        monkeypatch.setattr(
            _qtw.QMessageBox, "question", lambda *_: _qtw.QMessageBox.No
        )
        ddckFilePath.write_text("CONSTANTS 1\nchanged = 1\n")
        editorTab._onFileChangedOnDisk(str(ddckFilePath))

        assert document.getText().endswith("! mine")
        assert document.isModified

    def testMaybeSaveAllCanBeCancelled(
        self, editorTab, ddckFilePath, monkeypatch
    ):
        editorTab.openFile(ddckFilePath)
        editorTab._getCurrentDocument().editor.appendPlainText("! mine")

        monkeypatch.setattr(
            _qtw.QMessageBox, "question", lambda *_: _qtw.QMessageBox.Cancel
        )
        assert not editorTab.maybeSaveAll()

        monkeypatch.setattr(
            _qtw.QMessageBox, "question", lambda *_: _qtw.QMessageBox.SaveAll
        )
        assert editorTab.maybeSaveAll()
        assert ddckFilePath.read_text().endswith("! mine")

    def testReplaceAllIsOneUndoStep(self, editorTab, ddckFilePath):
        editorTab.openFile(ddckFilePath)
        document = editorTab._getCurrentDocument()
        findBar = editorTab._findBar

        findBar._findEdit.setText("TIn")
        findBar._replaceEdit.setText("TInlet")
        assert findBar.replaceAll() == 2
        assert "TIn " not in document.getText()

        document.editor.undo()
        assert document.getText() == _VALID_DDCK

    def testWithoutDiagramValuesPlaceholdersNeedDefaults(
        self, qtbot, ddckFilePath
    ):
        editorTab = _tab.DdckEditorTab(lambda: None)
        qtbot.addWidget(editorTab)

        editorTab.openFile(ddckFilePath)

        assert editorTab._getCurrentDocument().problems
