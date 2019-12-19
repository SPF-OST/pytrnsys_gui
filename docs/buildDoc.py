import os

os.system('sphinx-apidoc -f -o . ../trnsysGUI')
os.system('make clean')
os.system('make html')

