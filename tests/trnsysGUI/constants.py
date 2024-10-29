import pathlib as _pl

import trnsysGUI as _GUI

REPO_ROOT = _pl.Path(_GUI.__file__).parents[1]
DATA_FOLDER = REPO_ROOT / "tests" / "trnsysGUI" / "data"

PATH_TO_SETTINGS_JSON = DATA_FOLDER / "settings.json"

PATH_TO_PROJECT_1 = DATA_FOLDER / "exampleProjects/example1/example1.json"
PATH_TO_PROJECT_2 = DATA_FOLDER / "exampleProjects/example2/example2.json"
PATH_TO_PROJECT_3 = DATA_FOLDER / "exampleProjects/example3/example3.json"
PATH_TO_DIAGRAM_WITH_TAP_FOR_REGIMES = DATA_FOLDER / "diagramWithTapForRegimes/diagramWithTapForRegimes.json"

EXPECTED_EXCEPTION_TEXT = (
    "[Errno 2] No such file or directory:"
    " 'C:\\\\Development\\\\parent\\\\pytrnsys_gui\\\\tests\\\\trnsysGUI\\\\data\\\\diagramWithTapForRegimes\\\\"
    "modes_template.csv'"
)
