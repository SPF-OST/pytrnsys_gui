import pathlib as _pl
import pprint as _pp

import xmlschema as _xml

import convertXmlTmfToDdck as _tmf

_CONTAINING_DIR_PATH = _pl.Path(__file__).parent


def testValidateXmlTmf() -> None:
    xsdFilePath = _CONTAINING_DIR_PATH / "xmltmf.xsd"
    schema = _xml.XMLSchema11(xsdFilePath)

    xmlFilePath = _CONTAINING_DIR_PATH / "Type71.xmltmf"
    schema.validate(xmlFilePath)


def testDecodeXmlTmf() -> None:
    xsdFilePath = _CONTAINING_DIR_PATH / "xmltmf.xsd"
    schema = _xml.XMLSchema11(xsdFilePath)

    xmlFilePath = _CONTAINING_DIR_PATH / "Type71.xmltmf"
    deserializedData = schema.to_dict(xmlFilePath)
    _pp.pprint(deserializedData, indent=4)


def testConvertXmlTmfStringToDdck() -> None:
    xmlFilePath = _CONTAINING_DIR_PATH / "Type71.xmltmf"
    xmlFileContent = xmlFilePath.read_text(encoding="utf8")

    actualDdckContent = _tmf.convertXmlTmfStringToDdck(xmlFileContent)

    expectedDdckFilePath = _CONTAINING_DIR_PATH / "Type71.ddck"
    expectedDdckContent = expectedDdckFilePath.read_text(encoding="utf8")

    assert actualDdckContent == expectedDdckContent
