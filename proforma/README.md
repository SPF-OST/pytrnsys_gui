### Introduction ###
A prototype script to convert a TRNSYS simulation studio Proforma in the XMLTMF format to a ddck:
`Type71.xmltmf` is converted to `Type71.ddck`.

The additional information needed for the conversion is contained within the `<hydraulicConnections>`
element. This element does not exist in Proformas yet and would have to be added.

### Installation ###

1. Install Python 3.9 64bit from here https://www.python.org/ftp/python/3.9.13/python-3.9.13-amd64.exe
2. Create a virtual environment:
    ```commandline
    py -3.9 -m venv venv
    ```
3. Activate the environment:
    ```commandline
    venv\Scripts\activate
    ```
4. Install the dependencies:
    ```commandline
    python -m pip install -r dev-requirements.txt
    ```

### Run tests ###
Run
```commandline
pytest -rA .
```
