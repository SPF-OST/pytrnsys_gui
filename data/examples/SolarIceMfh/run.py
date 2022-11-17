import pytrnsys.rsim.runParallelTrnsys as runTrnsys
import os, sys


if __name__ == '__main__':

    pathBase = os.getcwd()

    configFile = "run.config"

    nameDeck = "SolarIce"

    runTool = runTrnsys.RunParallelTrnsys(pathBase, nameDeck)

    runTool.readConfig(pathBase, configFile)

    runTool.getConfig()

    runTool.runConfig()

    runTool.runParallel()

