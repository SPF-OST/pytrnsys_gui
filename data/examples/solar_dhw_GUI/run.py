import os

from pytrnsys.rsim import runParallelTrnsys as runTrnsys
from pytrnsys.utils import log as log

if __name__ == "__main__":
    logger = log.getOrCreateCustomLogger("root", "INFO")

    logger.info("Running config file %s...", "run.config")

    nameDeck = "solar_DHW_gui"
    pathBase = os.getcwd()

    runTool = runTrnsys.RunParallelTrnsys(pathBase, nameDeck)

    runTool.readConfig(pathBase, "run.config")
    runTool.getConfig()
    runTool.runConfig()
    runTool.runParallel()

    logger.info("...DONE (%s).", "run.config")
