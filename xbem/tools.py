from xml.dom import minidom
from xml import sax
import urlparse
import os
from urllib2 import urlopen

from xbem.exceptions import *


SUPPORTED_SCHEMES = ("http", "https", "ftp")


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


def _remove_blank_nodes(node):
    tmp = node.firstChild

    while tmp is not None:
        if tmp.nodeType == 3 and tmp.nodeValue.strip() == "":
            tmp2 = tmp.nextSibling
            node.removeChild(tmp)
            tmp = tmp2
        else:
            _remove_blank_nodes(tmp)
            tmp = tmp.nextSibling


def parse_xml(filename, string=None, remove_blank_nodes=True):
    parser._xml_filename = filename
    if string is None:
        ret = minidom.parse(filename, parser)
    else:
        ret = minidom.parseString(string, parser)
    if remove_blank_nodes:
        _remove_blank_nodes(ret.firstChild)
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


def get_path(p1, p2):
    p2url = urlparse.urlparse(p2)

    if p2url.scheme in SUPPORTED_SCHEMES:
        return p2
    elif p2url.scheme:
        raise UnsupportedScheme(p2url.scheme, p2)

    p1url = urlparse.urlparse(p1)
    base = os.path.dirname(p1)

    if p1url.scheme in SUPPORTED_SCHEMES:
        return urlparse.urljoin(base, p2)
    elif p1url.scheme:
        raise UnsupportedScheme(p1url.scheme, p1)
    else:
        return os.path.abspath(os.path.join(base, p2))


def read_file(filename, save_to_file=None):
    url = urlparse.urlparse(filename)

    if url.scheme and not url.scheme in SUPPORTED_SCHEMES:
        raise UnsupportedScheme(url.scheme, filename)

    if url.scheme:
        f = urlopen(filename)
    else:
        f = open(filename, "rb")

    if save_to_file is None:
        ret = f.read()
    else:
        ret = None
        fout = open(save_to_file, "w")
        data = f.read(16384)

        while data:
            fout.write(data)
            data = f.read(16384)

        fout.close()

    f.close()

    return ret


def create_subdirectories(path, is_filename=True):
    if is_filename:
        path = os.path.dirname(path)
    if not os.path.isdir(path):
        os.makedirs(path, mode=0755)
