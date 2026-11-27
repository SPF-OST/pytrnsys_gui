# pylint: disable=invalid-name  # `tmp_path` fixture
import pathlib as _pl

import pytest as _pt

import trnsysGUI.runConfig as _rc
import trnsysGUI.runConfig.importing as _imp

_COLLECTOR_DDCK = (
    "*******************************\r\n"
    "** ASSIGN PATH$\\Solar\\db\\commented_out.txt 1\r\n"
    "EQUATIONS 1\r\n"
    "unitReadIAM = 26 ! \u00b0C\r\n"
    "ASSIGN PATH$\\Solar\\db\\TVP_IAM.txt unitReadIAM\r\n"
    'ASSIGN "PATH$\\Solar\\db\\sub\\data.dat" 27\r\n'
    "ASSIGN PATH$\\Weather\\weather.dat 28\r\n"
    "ASSIGN PATH$\\Solar\\db\\missing.txt 29\r\n"
    "ASSIGN C:\\absolute\\file.txt 30\r\n"
)


@_pt.fixture(name="library")
def _library(tmp_path) -> _pl.Path:
    libraryDirPath = tmp_path / "library"
    dbDirPath = libraryDirPath / "Solar" / "db"
    (dbDirPath / "sub").mkdir(parents=True)
    (libraryDirPath / "Weather").mkdir()

    (dbDirPath / "TVP.ddck").write_bytes(
        _COLLECTOR_DDCK.encode("windows-1252")
    )
    (dbDirPath / "TVP_IAM.txt").write_text("iam")
    (dbDirPath / "Other_IAM.txt").write_text("not referenced")
    (dbDirPath / "sub" / "data.dat").write_text("data")
    (libraryDirPath / "Weather" / "weather.dat").write_text("weather")

    return libraryDirPath


class TestLibraryReference:
    def testReferenceAlwaysHasAs(self, library):
        include = _imp.createLibraryReference(
            library, library / "Solar" / "db" / "TVP.ddck", "Coll"
        )

        assert include.toLine() == "COMMON$ Solar/db/TVP as Coll"

    def testCustomAlias(self, library):
        include = _imp.createLibraryReference(
            library, library / "Solar" / "db" / "TVP.ddck", "Coll", "Other"
        )

        assert include.alias == "Other"

    def testFileOutsideLibraryIsRejected(self, library, tmp_path):
        outside = tmp_path / "outside.ddck"
        outside.write_text("")

        with _pt.raises(_imp.DdckImportError):
            _imp.createLibraryReference(library, outside, "Coll")


class TestCopy:
    def testCopiesDdckAndAssignedDataFiles(self, library, tmp_path):
        projectDdckDirPath = tmp_path / "project" / "ddck"

        result = _imp.copyIntoProject(
            library,
            library / "Solar" / "db" / "TVP.ddck",
            projectDdckDirPath,
            "Coll",
        )

        collDirPath = projectDdckDirPath / "Coll"
        assert sorted(result.copiedFilePaths) == sorted(
            [
                collDirPath / "TVP.ddck",
                collDirPath / "TVP_IAM.txt",
                collDirPath / "sub" / "data.dat",
                collDirPath / "Weather" / "weather.dat",
            ]
        )
        assert not (collDirPath / "Other_IAM.txt").exists()
        assert result.include.toLine() == "PROJECT$ Coll/TVP"

        copiedBytes = (collDirPath / "TVP.ddck").read_bytes()
        assert copiedBytes == _COLLECTOR_DDCK.replace(
            "PATH$\\Solar\\db\\TVP_IAM.txt", "PATH$\\Coll\\TVP_IAM.txt"
        ).replace(
            '"PATH$\\Solar\\db\\sub\\data.dat"', '"PATH$\\Coll\\sub\\data.dat"'
        ).replace(
            "PATH$\\Weather\\weather.dat", "PATH$\\Coll\\Weather\\weather.dat"
        ).encode(
            "windows-1252"
        )

        (warning,) = result.warnings
        assert "missing.txt" in warning

    def testAliasOnlyWrittenIfDifferentFromComponent(self, library, tmp_path):
        ddckFilePath = library / "Solar" / "db" / "TVP.ddck"
        ddckDirPath = tmp_path / "ddck"

        same = _imp.copyIntoProject(
            library, ddckFilePath, ddckDirPath, "Coll", alias="Coll"
        )
        other = _imp.copyIntoProject(
            library,
            ddckFilePath,
            ddckDirPath,
            "Coll",
            alias="X",
            overwrite=True,
        )

        assert same.include.alias is None
        assert other.include.toLine() == "PROJECT$ Coll/TVP as X"

    def testExistingFilesAreNotOverwrittenUnlessAsked(self, library, tmp_path):
        ddckFilePath = library / "Solar" / "db" / "TVP.ddck"
        ddckDirPath = tmp_path / "ddck"
        _imp.copyIntoProject(library, ddckFilePath, ddckDirPath, "Coll")
        (ddckDirPath / "Coll" / "TVP.ddck").write_text("my changes")

        with _pt.raises(_imp.TargetFilesExistError) as error:
            _imp.copyIntoProject(library, ddckFilePath, ddckDirPath, "Coll")

        assert len(error.value.filePaths) == 4
        assert (ddckDirPath / "Coll" / "TVP.ddck").read_text() == "my changes"

        _imp.copyIntoProject(
            library, ddckFilePath, ddckDirPath, "Coll", overwrite=True
        )
        assert (ddckDirPath / "Coll" / "TVP.ddck").read_text() != "my changes"

    def testNonDdckIsRejected(self, library, tmp_path):
        with _pt.raises(_imp.DdckImportError):
            _imp.copyIntoProject(
                library,
                library / "Solar" / "db" / "TVP_IAM.txt",
                tmp_path,
                "Coll",
            )


class TestLibraryPathVariable:
    def testDefinedRelativeToConfig(self, library, tmp_path):
        projectDirPath = tmp_path / "projects" / "p1"
        projectDirPath.mkdir(parents=True)
        config = _rc.RunConfig("", projectDirPath / "run.config")

        warning = _imp.ensureLibraryPathVariable(config, library)

        assert warning is None
        assert config.getPathVariables()["COMMON$"] == str(
            _pl.Path("..") / ".." / "library"
        )

    def testSameLibraryIsAccepted(self, library, tmp_path):
        config = _rc.RunConfig(
            f'string COMMON$ "{library}"\n', tmp_path / "run.config"
        )

        assert _imp.ensureLibraryPathVariable(config, library) is None

    def testOtherLibraryIsKeptWithWarning(self, library, tmp_path):
        config = _rc.RunConfig(
            'string COMMON$ "C:/elsewhere"\n', tmp_path / "run.config"
        )

        warning = _imp.ensureLibraryPathVariable(config, library)

        assert "C:/elsewhere" in warning
        assert config.getPathVariables()["COMMON$"] == "C:/elsewhere"
