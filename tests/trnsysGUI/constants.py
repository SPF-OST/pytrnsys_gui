import pathlib as _pl
import trnsysGUI as _GUI

REPO_ROOT = _pl.Path(_GUI.__file__).parents[1]
DATA_FOLDER = REPO_ROOT / "tests" / "trnsysGUI" / "data"

PATH_TO_SETTINGS_JSON = DATA_FOLDER / "settings.json"

PROJECT_1 = DATA_FOLDER / "exampleProjects/example1/example1.json"
PROJECT_2 = DATA_FOLDER / "exampleProjects/example2/example2.json"
PROJECT_3 = DATA_FOLDER / "exampleProjects/example3/example3.json"
