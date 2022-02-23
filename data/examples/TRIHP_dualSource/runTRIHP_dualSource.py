# pylint: skip-file
# type: ignore

# -*- coding: utf-8 -*-
"""
Created on Fri Sep 30 10:06:47 2016

@author: dcarbone, mbattagl
"""

import pytrnsys.rsim.runParallelTrnsys as runTrnsys

import os

if __name__ == "__main__":

    pathConfig = os.getcwd()
    configFile = "run.config"
    runTool = runTrnsys.RunParallelTrnsys(pathConfig, configFile=configFile)
