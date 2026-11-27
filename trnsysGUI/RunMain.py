# pylint: skip-file
# type: ignore

import os
import pathlib as _pl

import pytrnsys.rsim.runParallelTrnsys as runTrnsys

import trnsysGUI.runConfig.sync as _sync


class RunMain:
    def runAction(self, logger, path, configFile="run.config"):
        """Runs the simulations of the run config `configFile` in the project
        directory `path`.

        pytrnsys is run from the project directory, so relative paths in the
        config (e.g. `string PROJECT$ "ddck"`) are relative to the project.

        Returns
        -------
        (bool, str)
            Whether the execution failed, and the error message.
        """
        fullPath = os.path.join(path, configFile)
        logger.info("Starting RunParallelTrnsys with " + fullPath)
        try:
            with _sync.workingDirectory(_pl.Path(path)):
                runTrnsys.RunParallelTrnsys(path, configFile=configFile)
            return False, ""
        except Exception as e:
            logger.error(
                "EXCEPTION WHILE TRYING TO EXECUTE RunParallelTrnsys: %s",
                str(e),
            )
            return True, str(e)
