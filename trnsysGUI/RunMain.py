import sys
sys.path.append('C:\\Users\\parad\\OneDrive\\Desktop\\pytrnsys\\pytrnsys')
import pytrnsys.rsim.runParallelTrnsys as runTrnsys

import os


class RunMain:

    def runAction(self, path):
        pathConfig = path
        configFile = "run.config"
        runTool = runTrnsys.RunParallelTrnsys(pathConfig,configFile=configFile)