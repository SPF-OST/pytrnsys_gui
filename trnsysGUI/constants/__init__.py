import enum as _enum

# Text for message box
UNSAVED_PROGRESS_LOST = (
    "Are you sure you want to open another project?"
    " Unsaved progress on the current one will be lost."
)
SAVE_BEFORE_CLOSE = "Do you want to save the current state of the project before closing the program?"
NO_PROPER_PROJECT_ENVIRONMENT = (
    "The json you are opening does not have a proper project folder environment."
    " Do you want to continue and create one?"
)
NO_RECENT_AVAILABLE = "No recent project available"
RECENT_MOVED_OR_DELETED = "Recent project has moved or was deleted, it will be removed from the list of recent projects"
DIRECTORY_MUST_BE_EMPTY = "The new project directory must be empty."
DEFAULT_MESSAGE_BOX_MESSAGE = "Do you want to proceed?"
DEFAULT_MESSAGE_BOX_TITLE = "Message"
MODES_CSV_CREATED = (
    "modes_template.csv has been created in your project directory"
)
MODES_CSV_CREATED_ADDITIONAL = (
    "Please rename (e.g. modes.csv) and provide pump and valve values"
)
MODE_CSV_ALREADY_EXISTS = "modes_template.csv file already exists in your project. Would you like to overwrite?"
ERROR_RUNNING_MODES = "Error running modes: "
ERROR_RUNNING_MODES_FILE_NOT_FOUND = f"{ERROR_RUNNING_MODES}file not found"
ERROR_RUNNING_MODES_TRNSYS_ADDITIONAL = (
    "There were issues with running the modes listed above, check the logs"
)


# Config
DEFAULT_MONOSPACED_FONT = "Courier New"
MODES_TEMPLATE_FILE_NAME = "modes_template.csv"


class CreateNewOrOpenExisting(_enum.Enum):
    CREATE_NEW = _enum.auto()
    OPEN_EXISTING = _enum.auto()
