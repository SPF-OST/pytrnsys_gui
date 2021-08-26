# pylint: skip-file
# type: ignore

import sys

sys.path.append("C:\\Users\\parad\\OneDrive\\Desktop\\pytrnsys\\pytrnsys")
import pytrnsys.rsim.runParallelTrnsys as runTrnsys

import os


class RunMain:
    def runAction(self, logger, path):
        """
        It uses the self-lines readed by readConfig and change the lines from source to end.
        This is used to change a ddck file readed for another. A typical example is the weather data file
        Parameters
        ----------
        source : str
            string to be replaced in the config file in the self.lines field
        end : str
            str to replace the source in the config file in the self.lines field

        Returns
        -------
        bool
        """

        pathConfig = path
        configFile = "run.config"
        fullPath = os.path.join(path, configFile)
        logger.info("Starting RunParallelTrnsys with " + fullPath)
        try:
            runTrnsys.RunParallelTrnsys(pathConfig, configFile=configFile)
            return False, ""
        except Exception as e:
            logger.error("EXCEPTION WHILE TRYING TO EXECUTE RunParallelTrnsys: %s", str(e))
            return True, str(e)
