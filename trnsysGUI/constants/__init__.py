import enum as _enum


UNSAVED_PROGRESS_LOST = (
    "Are you sure you want to open another project? Unsaved progress on the current one will be lost."
)
NO_PROPER_PROJECT_ENVIRONMENT = (
    "The json you are opening does not have a proper project folder environment."
    " Do you want to continue and create one?"
)
NO_RECENT_AVAILABLE = "No recent project available"
RECENT_MOVED_OR_DELETED = "Recent project has moved or was deleted"
DIRECTORY_MUST_BE_EMPTY = "The new project directory must be empty."

DEFAULT_MESSAGE_BOX_MESSAGE = "Do you want to proceed?"
DEFAULT_MESSAGE_BOX_TITLE = "Message"


class _CreateNewOrOpenExisting(_enum.Enum):
    CREATE_NEW = _enum.auto()
    OPEN_EXISTING = _enum.auto()
