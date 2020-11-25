import sys
sys.path.append('C:\\Users\\parad\\OneDrive\\Desktop\\pytrnsys\\pytrnsys')
import pytrnsys.rsim.runParallelTrnsys as runTrnsys
import pytrnsys.psim.processParallelTrnsys as processTrnsys

import os


class ProcessMain:

    def processAction(self, path):
        pathConfig = path
        configFile = "process.config"
        processTool = processTrnsys.ProcessParallelTrnsys()
        processTool.readConfig(pathConfig,configFile)
        processTool.process()