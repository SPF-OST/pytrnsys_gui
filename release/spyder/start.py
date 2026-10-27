import matplotlib_inline  # type: ignore[import-untyped]

import spyder.app.start as spyder  # type: ignore[import-untyped]

# Make inline plots work
# See here: https://github.com/spyder-ide/spyder/issues/22420#issuecomment-2562147200
matplotlib_inline.backend_inline.set_matplotlib_formats("svg")

spyder.main()
