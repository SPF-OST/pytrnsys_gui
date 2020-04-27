import os

if __name__ == '__main__':
    ROOT_DIR = os.path.dirname(__file__)
    print(ROOT_DIR)
    os.system("start cmd")
    os.system("cd %s" % ROOT_DIR)
    os.system("pyinstaller --onefile GUI.spec")


