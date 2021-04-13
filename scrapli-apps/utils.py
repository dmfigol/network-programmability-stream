from typing import Any, Optional, Union
from xml.dom.minidom import parseString

from lxml import etree
from ruamel.yaml import YAML


def dict_to_xml(
    data: Any, root: Union[None, str, etree._Element] = None, attr_marker: str = "_"
) -> etree._Element:
    """Converts Python dictionary with YANG data to lxml etree.Element object.
    XML attributes must be represented in nested dictionary, which is accessed by the
    element name. Attribute keys must be prepended with underscore. Common use-cases:
      * operation attribute. For example:
        {"vrf": {"_operation": "replace"}} -> <vrf operation="replace"></vrf>
      * changing default namespace. For example:
        {"native": {"hostname": "R1", "_xmlns": "http://cisco.com/ns/yang/Cisco-IOS-XE-native"}} ->
        <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native"><hostname>R1</hostname></native>
    Empty XML tags (including self-closing tags) are represented with value `None`:
       {"address-family": {"ipv4": None}} -> <address-family><ipv4/></address-family>
    When an element has attributes, it can't be simply represented with key-value pair,
    instead use #text key, for example:
        {"bundle-name": {
            "_xmlns": "http://cisco.com/ns/yang/Cisco-IOS-XE-ppp",
            "#text": "authenticated"
        }} ->
        <bundle-name xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-ppp">authenticated</bundle-name>
    Namespaces with prefix:
      1. They need to be defined under the top-level key "_namespaces" in the dictionary
         in the form prefix:namespace. E.g.:
         {"_namespaces": {"ianaift": "urn:ietf:params:xml:ns:yang:iana-if-type"}}
      2. Use the form `element-name+prefix` to use it for a specific element. E.g.:
         {"type+ianaift": "ianaift:ethernetCsmacd"} ->
         <type ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:ethernetCsmacd</type>
    """
    namespaces = data.pop("_namespaces", {})

    def _dict_to_xml(data_: Any, parent: Optional[etree._Element] = None) -> None:
        nonlocal root
        if not isinstance(data_, dict):
            raise ValueError("provided data must be a dictionary")

        for key, value in data_.items():
            if key.startswith(attr_marker):
                # handle keys starting with attr_marker as tag attributes
                attr_name = key.lstrip(attr_marker)
                parent.attrib[attr_name] = value
            elif key == "#text":
                parent.text = value
            else:
                if "+" in key:
                    key, *_namespaces = key.split("+")
                    nsmap = {ns: namespaces[ns] for ns in _namespaces}
                else:
                    nsmap = None
                element = etree.Element(key, nsmap=nsmap)
                if root is None:
                    root = element

                if parent is not None and not isinstance(value, list):
                    parent.append(element)

                if isinstance(value, dict):
                    _dict_to_xml(value, element)
                elif isinstance(value, list):
                    for item in value:
                        list_key = etree.Element(key)
                        parent.append(list_key)
                        _dict_to_xml(item, list_key)
                else:
                    if value is True or value is False:
                        value = str(value).lower()
                    elif value is not None and not isinstance(value, str):
                        value = str(value)

                    element.text = value

    if isinstance(root, str):
        root = etree.Element(root)
    _dict_to_xml(data, root)
    return root


def prettify_xml(xml: Union[str, etree._Element]) -> str:
    if isinstance(xml, etree._Element):
        result = etree.tostring(xml, pretty_print=True).decode("utf-8")
    else:
        result = parseString(xml).toprettyxml()
    return result


def yaml_to_xml_str(
    yaml_content: str, root: Union[None, str, etree._Element] = None
) -> str:
    yml = YAML(typ="safe")
    data = yml.load(yaml_content)
    _xml = dict_to_xml(data=data, root=root)
    result = etree.tostring(_xml).decode("utf-8")
    return result
