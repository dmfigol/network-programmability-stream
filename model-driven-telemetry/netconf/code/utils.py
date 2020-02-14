from typing import Union
from xml.dom.minidom import parseString

from lxml import etree


def prettify_xml(xml: Union[str, etree._Element]) -> str:
    if isinstance(xml, etree._Element):
        result = etree.tostring(xml, pretty_print=True).decode("utf-8")
    else:
        result = parseString(xml).toprettyxml("  ")
    return result