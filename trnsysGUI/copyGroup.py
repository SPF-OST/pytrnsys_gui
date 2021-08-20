# pylint: skip-file
# type: ignore

class copyGroup:
    def __init__(self, editor):
        self.diagramName = "COPYGROUP"
        # self.diagramEditor = editor
        self.trnsysObj = []
        self.groupList = []
        self.idGen = editor.idGen
        self.graphicalObj = []
