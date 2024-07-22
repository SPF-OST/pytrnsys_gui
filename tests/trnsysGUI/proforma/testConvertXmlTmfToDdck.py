import pathlib as _pl
import pprint as _pp
import pkgutil as _pu

import xmlschema as _xml

import trnsysGUI.proforma.convertXmlTmfToDdck as _pc

_CONTAINING_DIR_PATH = _pl.Path(__file__).parent


def testValidateXmlTmf() -> None:
    schema = _getSchema()

    xmlFilePath = _CONTAINING_DIR_PATH / "Type71.xmltmf"
    schema.validate(xmlFilePath)


def testDecodeXmlTmf() -> None:
    schema = _getSchema()

    xmlFilePath = _CONTAINING_DIR_PATH / "Type71.xmltmf"
    deserializedData = schema.to_dict(xmlFilePath)
    _pp.pprint(deserializedData, indent=4)


def _getSchema() -> _xml.XMLSchema11:
    data = _pu.get_data(_pc.__name__, "xmltmf.xsd")
    string = data.decode("UTF8")
    schema = _xml.XMLSchema11(string)
    return schema


def testConvertXmlTmfStringToDdck() -> None:
    xmlFilePath = _CONTAINING_DIR_PATH / "Type71.xmltmf"
    xmlFileContent = xmlFilePath.read_text(encoding="utf8")

    actualDdckContent = _pc.convertXmlTmfStringToDdck(xmlFileContent)

    expectedDdckFilePath = _CONTAINING_DIR_PATH / "Type71.ddck"
    expectedDdckContent = expectedDdckFilePath.read_text(encoding="utf8")

    assert actualDdckContent == expectedDdckContent
