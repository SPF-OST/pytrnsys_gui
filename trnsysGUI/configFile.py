# pylint: skip-file
# type: ignore

import os
import glob
from PyQt5.QtWidgets import *


class configFile:
    def __init__(self, configPath, editor):
        self.projectFolder = os.path.split(configPath)[0]
        self.editor = editor
        self.configPath = configPath
        if os.path.isfile(self.configPath):
            infile = open(self.configPath, "r")
            self.lines = infile.readlines()
            self.fileExists = True
            self.updateConfig()
        else:
            self.fileExists = False
            qmb = QMessageBox()
            qmb.setText("Please add run.config in %s" % self.projectFolder)
            qmb.setStandardButtons(QMessageBox.Ok)
            qmb.setDefaultButton(QMessageBox.Ok)
            qmb.exec()

    def statementChecker(self, keyword):
        for i in range(len(self.lines)):
            if keyword in self.lines[i]:
                return i
        return -1

    def updateConfig(self):
        """
        Updates the run.config-file with the current project folder, the nameRef, and the projectFolder and adds the
        ddcks of the current project.

        Parameters
        ----------

        Returns
        -------

        """
        originalNumberOfLines = len(self.lines)
        for i in range(originalNumberOfLines):
            try:
                if self.lines[originalNumberOfLines - 1 - i][:9] == "PROJECT$ ":
                    del self.lines[originalNumberOfLines - 1 - i]
            except:
                pass

        ddckPath = os.path.join(self.projectFolder, "ddck")

        linePaths = self.statementChecker("#PATHS#")
        if linePaths == -1:
            self.lines += [
                "\n",
                "##################PATHS##################",
                "\n",
                "\n",
                'string PROJECT$ "%s"\n' % ddckPath,
            ]
        else:
            lineProjectPathDdck = self.statementChecker("PROJECT$ ")
            if lineProjectPathDdck == -1:
                self.lines.insert(linePaths + 2, 'string PROJECT$ "%s"\n' % ddckPath)
            else:
                self.lines[lineProjectPathDdck] = 'string PROJECT$ "%s"\n' % ddckPath

        lineNameRef = self.statementChecker("string nameRef")
        if lineNameRef != -1:
            self.lines[lineNameRef] = 'string nameRef "%s"\n' % os.path.split(self.projectFolder)[-1]

        lineProjectPath = self.statementChecker("string projectPath")
        if lineProjectPath == -1:
            self.lines.insert(lineNameRef, 'string projectPath "%s"\n' % self.projectFolder)
        else:
            self.lines[lineProjectPath] = 'string projectPath "%s"\n' % self.projectFolder

        lineDdck = self.statementChecker("USED DDCKs")
        if lineDdck == -1:
            self.lines += ["\n", "#############USED DDCKs##################", "\n", "\n", "\n"]
            lineDdck = len(self.lines) - 2

        ddckFiles = glob.glob(os.path.join(ddckPath, "**/*.ddck"), recursive=True)
        for i in range(len(ddckFiles)):
            ddckFiles[i] = ddckFiles[i].replace(ddckPath + "\\", "")
            ddckFiles[i] = ddckFiles[i].replace(".ddck", "")
        for i in range(len(ddckFiles)):
            if "head" in ddckFiles[i]:
                ddckFiles.insert(0, ddckFiles.pop(i))
        for i in range(len(ddckFiles)):
            if "end" in ddckFiles[i]:
                ddckFiles.insert(len(ddckFiles) - 1, ddckFiles.pop(i))
        ddcksEntered = 0
        for ddck in ddckFiles:
            self.lines.insert(lineDdck + 2 + ddcksEntered, "PROJECT$ " + ddck + "\n")
            ddcksEntered += 1

        outfile = open(self.configPath, "w")
        outfile.writelines(self.lines)
        outfile.close()

        # def checkConfigDuplicate(self, lines, keyword, replacement):
        #     """
        #     Checks whether a certain keyword occurs in a file split into lines. If the keyword appears in a line, this line
        #     is replaced with the replacement. It returns a Boolean that is true, if the statement was in none of the lines.
        #
        #     Parameters
        #     ----------
        #     lines : list of str
        #     keyword : str
        #     replacement : str
        #
        #     Returns
        #     -------
        #     notInConfigFile : bool
        #
        #     """
        #     notInConfigFile = True
        #     for i in range(len(lines)):
        #         if keyword in lines[i]:
        #             lines[i] = replacement
        #             notInConfigFile = False
        #     return notInConfigFile
