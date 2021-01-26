import os

os.system('sphinx-apidoc -f -o ./')
os.system('make clean')
os.system('make html')
#os.system('make pdf')

