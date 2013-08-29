from xbem.ns import *
from xbem.decl import DeclarationBlock
from xbem.tools import parse_xml, get_node_text, read_file, get_path
from xbem.exceptions import *


class RepositorySource(object):
    def __init__(self, filename):
        self.filename = filename
        self.read_source(parse_xml(filename, read_file(filename)))

    def __repr__(self):
        return "RepositorySource('%s')" % self.filename

    def read_source(self, repo):
        self.blocks = {}

        node = repo.firstChild

        if node.namespaceURI != XBEM_REPO_NAMESPACE:
            raise UnexpectedNodeException(node)
        if node.localName != "blocks":
            raise UnexpectedNodeException(node)

        node = node.firstChild

        while node is not None:
            if node.namespaceURI != XBEM_REPO_NAMESPACE:
                raise UnexpectedNodeException(node)
            if node.localName != "block":
                raise UnexpectedNodeException(node)

            node2 = node.firstChild

            if node2 is None:
                raise EmptyNodeException(node)

            block = None
            filename = None

            while node2 is not None:
                if node2.namespaceURI != XBEM_REPO_NAMESPACE:
                    raise UnexpectedNodeException(node2)
                if node2.localName == "name":
                    if block is None:
                        block = get_node_text(node2)
                    else:
                        raise UnexpectedNodeException(node2)
                elif node2.localName == "file":
                    if filename is None:
                        filename = get_node_text(node2)
                    else:
                        raise UnexpectedNodeException(node2)
                else:
                    raise UnexpectedNodeException(node2)

                node2 = node2.nextSibling

            if block is None:
                raise NoNameNodeException(node)
            if filename is None:
                raise CustomNodeException(node, "No filename")

            if block in self.blocks:
                raise CustomNodeException(node, "Duplicate block")

            self.blocks[block] = {
                "filename": get_path(self.filename, filename),
                "loaded": None
            }

            node = node.nextSibling
        print self.blocks

    def get_block(self, name):
        block = self.blocks.get(name)

        if block is None:
            return None

        if block["loaded"] is None:
            block["loaded"] = DeclarationBlock(block["filename"])

        return block["loaded"]


class Repository(object):
    def __init__(self, parent=None):
        self.sources = [] if parent is None else parent.sources[:]

    def __repr__(self):
        return "Repository(%s)" % self.sources

    def add_source(self, filename):
        self.sources.append(RepositorySource(filename))

    def get_block(self, name):
        for src in self.sources[::-1]:
            block = src.get_block(name)
            if block is not None:
                return block
        return None
