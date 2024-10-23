# pylint: skip-file
# type: ignore

import pytrnsys.rsim.runParallelTrnsys as runTrnsys
import os

pathConfig = "./"

configFile = "run.config"

runTool = runTrnsys.RunParallelTrnsys(pathConfig, configFile=configFile)
