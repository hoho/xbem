from xml.dom import minidom
from xml import sax
from xbem.exceptions import *


def _set_content_handler(dom_handler):
    def startElementNS(name, tagName, attrs):
        orig_start_cb(name, tagName, attrs)
        elem = dom_handler.elementStack[-1]
        elem.filename = parser._xml_filename
        elem.lineNo = parser._parser.CurrentLineNumber
        elem.colNo = parser._parser.CurrentColumnNumber

    orig_start_cb = dom_handler.startElementNS
    dom_handler.startElementNS = startElementNS
    orig_set_content_handler(dom_handler)


def remove_empty_text_nodes(node):
    tmp = node.firstChild

    while tmp is not None:
        if tmp.nodeType == 3 and tmp.nodeValue.strip() == "":
            tmp2 = tmp.nextSibling
            node.removeChild(tmp)
            tmp = tmp2
        else:
            remove_empty_text_nodes(tmp)
            tmp = tmp.nextSibling


def parse_xml(filename):
    parser._xml_filename = filename
    ret = minidom.parse(filename, parser)
    remove_empty_text_nodes(ret.firstChild)
    return ret


parser = sax.make_parser()
orig_set_content_handler = parser.setContentHandler
parser.setContentHandler = _set_content_handler


def get_node_text(node):
    if node.firstChild is not None:
        if node.firstChild.nodeType != 3:
            raise UnexpectedNodeException(node.firstChild)
        if node.firstChild.nextSibling is not None:
            raise UnexpectedNodeException(node.firstChild.nextSibling)
        ret = (node.firstChild.nodeValue or "").strip()
        if not ret:
            raise EmptyNodeException(node)
        return ret
    else:
        raise EmptyNodeException(node)
