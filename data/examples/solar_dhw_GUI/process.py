import os
import sys

from pytrnsys.psim import processParallelTrnsys as pParallelTrnsys

# multiprocessing bug? See: https://github.com/python/cpython/issues/87115
__spec__ = None

if __name__ == "__main__":
    configName = sys.argv[1]

    pathBase = os.getcwd()
    print(pathBase)

    tool = pParallelTrnsys.ProcessParallelTrnsys()
    tool.readConfig(pathBase, configName)
    tool.process()
