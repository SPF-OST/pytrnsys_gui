# pylint: skip-file
# type: ignore

import random

from trnsysGUI.Connection import Connection


class PipeDataHandler(object):
    def __init__(self, diagramEditor):
        self.massflowFilePath = "massflowData/flows.txt"
        self.timeSteps = 365
        self.diagramEditor = diagramEditor

    def clearFile(self):
        f = open(self.massflowFilePath, "w")
        f.truncate(0)
        f.close()

    def generateData(self):
        self.clearFile()
        f = open(self.massflowFilePath, "w")
        for ts in range(self.timeSteps):
            for t in self.diagramEditor.trnsysObj:
                if isinstance(t, Connection):
                    if ts != 100:
                        a = random.random()
                    else:
                        a = 0

                    if a < 1 / 3:
                        a = -1e3
                    elif 1 / 3 <= a <= 2 / 3:
                        a = 0
                    else:
                        a = 1e3
                    f.write(str(a) + " " * (10 - len(str(a))))

            f.write("\n")

        f.close()
