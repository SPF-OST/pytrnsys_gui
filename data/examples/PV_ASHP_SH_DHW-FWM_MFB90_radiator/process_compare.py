# pylint: skip-file
# type: ignore

from pytrnsys.psim import processParallelTrnsys as pParallelTrnsys


if __name__ == "__main__":

    pathConfig = "./"
    tool = pParallelTrnsys.ProcessParallelTrnsys()
    tool.readConfig(pathConfig, "process_compare.config")
    tool.process()