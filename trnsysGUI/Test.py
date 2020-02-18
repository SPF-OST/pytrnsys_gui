import filecmp
import os
import sys


class Test(object):

    testPassed = True

    def retrieveFiles(self, exportedFilepath, originalFilePath, exportedFileList, originalFileList):
        for efiles in os.listdir(exportedFilepath):
            if efiles != '.keepMe':
                # exportedFile = exportedFilepath + efiles
                exportedFile = os.path.join(exportedFilepath, efiles)
                if exportedFile not in exportedFileList:
                    exportedFileList.append(exportedFile)

        for ofiles in os.listdir(originalFilePath):
            # originalFile = originalFilePath + ofiles
            originalFile = os.path.join(originalFilePath, ofiles)
            if originalFile not in originalFileList:
                originalFileList.append(originalFile)

        self.sortList(exportedFileList, originalFileList)

    def checkFileExists(self, exportedFileList, originalFileList):
        i = 0
        exportedFile = exportedFileList.split('\\')
        while i < len(originalFileList):
            referenceFile = originalFileList[i].split('\\')
            if exportedFile[-1] == referenceFile[-1]:
                return True
            i += 1
        return False

    def checkFiles(self, exportedFileList, originalFileList):
        i = 0
        fileErrorList = []
        found = False
        while i < len(exportedFileList):
            j = 0
            while j < len(originalFileList):
                exportedFile = exportedFileList[i].split('\\')[-1]
                referencefile = originalFileList[j].split('\\')[-1]
                # print('this is exported :' + exportedFile + '\n')
                # print('this is reference :' + referencefile + '\n')
                if exportedFile != referencefile:
                    j += 1
                else:
                    found = True
                    break
            if found:
                if not filecmp.cmp(exportedFileList[i], originalFileList[j], shallow=False):
                    self.testPassed = False
                    fileErrorList.append(i)
                    # break
            i += 1
        return fileErrorList, self.testPassed
        # return i, self.testPassed

    def deleteFiles(self, fileDirectory):
        for dfiles in os.listdir(fileDirectory):
            # deleteFiles = fileDirectory + dfiles
            deleteFiles = os.path.join(fileDirectory, dfiles)
            if dfiles != '.keepMe':
                os.remove(deleteFiles)


    def showDifference(self, file1, file2):
        line = 1
        fileOne = open(file1)
        fileTwo = open(file2)

        file1List = []
        file2List = []

        fileOneLine = fileOne.readline()
        fileTwoLine = fileTwo.readline()

        while fileOneLine:
            if fileOneLine != fileTwoLine:
                print("Error found at line %d\n" % line)
                print("Exported file: %s \nReference file: %s \n" % (fileOneLine, fileTwoLine))
                file1Str = str(line) + ',' + fileOneLine
                file2Str = str(line) + ',' + fileTwoLine
                file1List.append(file1Str)
                file2List.append(file2Str)
            fileOneLine = fileOne.readline()
            fileTwoLine = fileTwo.readline()
            line += 1

        # print("File 1 list:")
        # print(file1List)
        # print("\nFile 2 List:")
        # print(file2List)

        fileOne.close()
        fileTwo.close()

        return file1List, file2List

    def sortList(self, list1, list2):
        list1.sort()
        list2.sort()
