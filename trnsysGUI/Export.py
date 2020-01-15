from trnsysGUI.Pump import Pump
from trnsysGUI.TVentil import TVentil
from trnsysGUI.WTap_main import WTap_main


class Export(object):
    def __init__(self, objList):
        self.trnsysObj = objList

    def exportBlackBox(self):
        f = "*** Black box component temperatures" + "\n"
        equationNr = 0

        for t in self.trnsysObj:
            f += t.exportBlackBox()[0]
            equationNr += t.exportBlackBox()[1]

        f = "\nEQUATIONS " + str(equationNr) + "\n" + f + "\n"

        return f

    def exportPumpOutlets(self):
        f = "*** Pump outlet temperatures" + "\n"
        equationNr = 0
        for t in self.trnsysObj:
            f += t.exportPumpOutlets()[0]
            equationNr += t.exportPumpOutlets()[1]

        f = "EQUATIONS " + str(equationNr) + "\n" + f + "\n"
        return f

    def exportMassFlows(self): # What the controller should give
        f = "*** Massflowrates" + "\n"
        equationNr = 0

        for t in self.trnsysObj:
            f += t.exportMassFlows()[0]
            equationNr += t.exportMassFlows()[1]

        f = "EQUATIONS " + str(equationNr) + "\n" + f + "\n"

        return f

    def exportDivSetting(self, unit):
        """

        :param unit: the index of the previous unit number used.
        :return:
        """

        nUnit = unit
        f = ""
        constants = 0
        f2 = ""
        for t in self.trnsysObj:
            f += t.exportDivSetting1()[0]
            constants += t.exportDivSetting1()[1]

        if constants > 0:
            f = "CONSTANTS " + str(constants) + "\n"
            f += f2 + "\n"

        for t in self.trnsysObj:
            res = t.exportDivSetting2(nUnit)
            f += res[0]
            nUnit = res[1]

        return f + "\n"
