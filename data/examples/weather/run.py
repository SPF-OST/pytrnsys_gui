# pylint: skip-file
# type: ignore

import pytrnsys.rsim.runParallelTrnsys as runTrnsys
import os

if __name__ == "__main__":

    pathConfig = "./"
    configFile = "run.config"

    runTool = runTrnsys.RunParallelTrnsys(pathConfig, configFile=configFile)
