# pylint: skip-file
# type: ignore

from pytrnsys.psim import processParallelTrnsys as pParallelTrnsys
import os


if __name__ == "__main__":

   # pathConfig = os.getcwd()
    pathConfig = "./"


    tool = pParallelTrnsys.ProcessParallelTrnsys()
    tool.readConfig(pathConfig, "process.config")
    tool.process()
