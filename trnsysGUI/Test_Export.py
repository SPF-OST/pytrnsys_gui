# pylint: skip-file
# type: ignore

import filecmp
import os


class Test_Export(object):
    """
    Just a class that contains the method for testing.
    No need to declare or pass anything.
    Parameters should be passed into the individual functions to avoid unnecessary instantiotion
    of class.
    """

    testPassed = True

    def retrieveFiles(self, exportedFilepath, originalFilePath, exportedFileList, originalFileList):
        """

        Parameters
        ----------
        exportedFilepath : Folder where files are exported to
        originalFilePath : Folder containing the reference files
        exportedFileList : List of files inside the exported folder
        originalFileList : List of files inside the reference folder

        1.Access the exported folder
        2.Retrieve all exported files and add into a list
        3.Access the reference folder
        4.Retrieve all reference files and add into a list
        5.Sort the two lists

        Returns
        -------

        """
        for efiles in os.listdir(exportedFilepath):
            if efiles != ".keepMe":
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

    def checkFileExists(self, exportedFile, originalFileList):
        """

        Parameters
        ----------
        exportedFile : ONE FILE from the export_test folder
        originalFileList : list of files inside the reference folder

        1.Check if the individual files inside the export_test folder can be found
        inside the reference folder as well.
        2.If found, return true.
        3.Else, return false.

        Returns
        -------

        """
        i = 0
        exportedFile = exportedFile.split("\\")
        while i < len(originalFileList):
            referenceFile = originalFileList[i].split("\\")
            if exportedFile[-1] == referenceFile[-1]:
                return True
            i += 1
        return False

    def checkFiles(self, exportedFileList, originalFileList):
        """

        Parameters
        ----------
        exportedFileList : All files inside the export_test folder
        originalFileList : All files inside the reference folder

        1.Check each exported file against the reference file of the same name
        2.If two files of the same name from both folders are found, check their contents
        3.If the contents are not the same, append the file index(order inside the folder) into fileErrorList
          and set testPassed to False
        4.Return fileErrorList and testPassed attribute

        Returns
        -------

        """

        i = 0
        fileErrorList = []
        found = False
        while i < len(exportedFileList):
            j = 0
            while j < len(originalFileList):
                exportedFile = exportedFileList[i].split("\\")[-1]
                referencefile = originalFileList[j].split("\\")[-1]
                # print('this is exported :' + exportedFile + '\n')
                # print('this is reference :' + referencefile + '\n')
                if exportedFile != referencefile:
                    j += 1
                else:
                    found = True
                    break
            if found:
                if not filecmp.cmp(exportedFileList[i], originalFileList[j], shallow=False):
                    # todo : can maybe simplify this part is not using random number for pump power
                    fileOne = open(exportedFileList[i])
                    fileTwo = open(originalFileList[j])

                    fileOneLine = fileOne.readline()
                    fileTwoLine = fileTwo.readline()

                    while fileOneLine:
                        if fileOneLine != fileTwoLine:
                            if fileOneLine.split(" = ")[0][:5] != "MfrPu":
                                self.testPassed = False
                                fileErrorList.append(i)
                                break

                        fileOneLine = fileOne.readline()
                        fileTwoLine = fileTwo.readline()
                    # break
            i += 1
        return fileErrorList, self.testPassed
        # return i, self.testPassed

    def deleteFiles(self, fileDirectory):
        """

        Parameters
        ----------
        fileDirectory : A specified file directory

        1.Delete every files inside the specified file directory

        Returns
        -------

        """
        for dfiles in os.listdir(fileDirectory):
            # deleteFiles = fileDirectory + dfiles
            deleteFiles = os.path.join(fileDirectory, dfiles)
            if dfiles != ".keepMe":
                os.remove(deleteFiles)

    def showDifference(self, file1, file2):
        """

        Parameters
        ----------
        file1 : exported file
        file2 : reference file

        1.Read a line from exported file and reference file
        2.Compare the two lines, if they are identical, go to next line.
        3.Else, Append the lines with their line number into two separate list.
        4.Close the files and return the two lists.

        Returns
        -------

        """
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
                if fileOneLine.split(" = ")[0][:5] != "MfrPu":
                    file1Str = str(line) + ":" + fileOneLine
                    file2Str = str(line) + ":" + fileTwoLine
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
