from abc import ABCMeta, abstractmethod, abstractproperty
import os

from xbem.ns import *
from xbem.exceptions import *
from xbem.deps import Dependencies
from xbem.tools import get_node_text, read_file, create_subdirectories

PROPERTY_STRING = 1
PROPERTY_EXISTING_FILE = 2
PROPERTY_EXISTING_DIRECTORY = 3
PROPERTY_NEW_FILE_OR_DIRECTORY = 4
PROPERTY_DIRECTORY = 4


class AbstractBuildTech(object):
    __metaclass__ = ABCMeta

    NAME = None
    PROPERTIES = {}

    def __init__(self, node):
        self.props = {}

        if node.namespaceURI != XBEM_BUILD_NAMESPACE:
            raise UnexpectedNodeException(node)
        if node.localName != self.NAME:
            raise UnexpectedNodeException(node)

        node = node.firstChild

        while node is not None:
            if node.namespaceURI != XBEM_BUILD_NAMESPACE:
                raise UnexpectedNodeException(node)

            prop_type = self.PROPERTIES.get(node.localName)
            if prop_type is None or prop_type in self.props:
                raise UnexpectedNodeException(node)

            prop = get_node_text(node)
            if prop_type != PROPERTY_STRING:
                prop = os.path.normpath(os.path.abspath(prop))
                err_msg = None

                if prop_type == PROPERTY_EXISTING_FILE:
                    if not os.path.isfile(prop):
                        err_msg = "'%s' is not a file"
                elif prop_type == PROPERTY_EXISTING_DIRECTORY:
                    if not os.path.isdir(prop):
                        err_msg = "'%s' is not a directory"
                elif prop_type == PROPERTY_NEW_FILE_OR_DIRECTORY:
                    if os.path.exists(prop):
                        err_msg = "'%s' should not exist"

                if err_msg is not None:
                    raise CustomNodeException(node, err_msg % prop)

            self.props[node.localName] = prop

            node = node.nextSibling

    @abstractmethod
    def build(self, deps, repo):
        pass


class BuildTech(AbstractBuildTech):
    @abstractproperty
    def get_deps(self, repo):
        pass


class BundleBuildTech(AbstractBuildTech):
    PROPERTIES = {
        "out": PROPERTY_NEW_FILE_OR_DIRECTORY,
        "rel": PROPERTY_STRING
    }

    def __init__(self, bundle, node):
        self.bundle = bundle
        super(BundleBuildTech, self).__init__(node)

    def get_filenames(self, deps):
        return deps.get_filenames(self.NAME, self.bundle.name)


class ConcatFilesBundleBuildTech(BundleBuildTech):
    @abstractmethod
    def get_file_comment(self, filename):
        pass

    def build(self, deps, repo):
        filenames = self.get_filenames(deps)
        if len(filenames) == 0:
            raise Exception("No %s files for bundle '%s'" %
                            (self.NAME, self.bundle.name))
        filename = self.props["out"]
        create_subdirectories(filename)
        out = open(filename, "w")
        for f in filenames:
            out.write("%s\n" % self.get_file_comment(f))
            out.write(read_file(f))
            out.write("\n\n")
        out.close()


class XMLDependenciesExtractor(object):
    def __init__(self, repo, node, no_imports=False):
        self.no_imports = no_imports
        self.deps = Dependencies(repo)
        self.extract(node)

    def get_deps(self):
        return self.deps

    def other(self, node, namespaces):
        pass

    def extract(self, node, namespaces=None):
        if node is None:
            return
        if namespaces is None:
            namespaces = {}
        newnamespaces = {}

        attrs = node.attributes
        if attrs is not None:
            for i in xrange(attrs.length):
                attr = attrs.item(i)
                if attr.prefix == "xmlns":
                    ns = namespaces.get(attr.value)
                    if ns is None or attr.localName not in ns:
                        newns = newnamespaces.get(attr.value)
                        if newns is None:
                            newnamespaces[attr.value] = set([attr.localName])
                        else:
                            newns.add(attr.localName)

        for ns, newprefixes in newnamespaces.iteritems():
            prefixes = namespaces.get(ns)
            namespaces[ns] = newprefixes if prefixes is None else \
                             prefixes.union(newprefixes)

        self._extract_callback(node, namespaces)

        tmp = node.firstChild
        while tmp is not None:
            self.extract(tmp, namespaces)
            tmp = tmp.nextSibling

        for ns, newprefixes in newnamespaces.iteritems():
            prefixes = namespaces.get(ns)
            if prefixes == newprefixes:
                del namespaces[ns]
            else:
                namespaces[ns] -= prefixes

    def _extract_callback(self, node, namespaces):
        b = namespaces.get(XBEM_BLOCK_NAMESPACE) or set()
        e = namespaces.get(XBEM_ELEMENT_NAMESPACE) or set()
        if node.prefix not in b and node.prefix not in e:
            self.other(node, namespaces)
            return

        m = namespaces.get(XBEM_MODIFIER_NAMESPACE)
        block_name = elem_name = None
        mods = []

        if node.prefix in b and node.localName != "block":
            raise UnexpectedNodeException(node)
        elif node.prefix in e and node.localName != "element":
            raise UnexpectedNodeException(node)

        for i in xrange(node.attributes.length):
            attr = node.attributes.item(i)
            unexpected = False

            if attr.prefix in b:
                if attr.localName == "name" and block_name is None:
                    block_name = attr.value
                else:
                    unexpected = True
            elif attr.prefix in e:
                if attr.localName == "name" and elem_name is None:
                    elem_name = attr.value
                else:
                    unexpected = True
            elif attr.prefix in m:
                mods.append((attr.localName, attr.value))

            if unexpected:
                raise CustomNodeException(node,
                                          "Unexpected '%s:%s' attribute" %
                                          (attr.prefix, attr.localName))

        if block_name is None:
            raise CustomNodeException(node, "No block name")
        if node.prefix in e and elem_name is None:
            raise CustomNodeException(node, "No element name")

        self.deps.append(block_name)

        if elem_name is not None:
            self.deps.append(block_name, elem_name)

        for mod, val in mods:
            self.deps.append(block_name, elem_name, mod)
            if val:
                self.deps.append(block_name, elem_name, mod, val)
