from abc import ABCMeta, abstractmethod, abstractproperty
import os

from xbem.ns import *
from xbem.exceptions import *
from xbem.tools import get_node_text, read_file

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
    def build(self, deps):
        pass


class BuildTech(AbstractBuildTech):
    @abstractproperty
    def get_deps(self, blocks_repos):
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

    def build(self, deps):
        filenames = self.get_filenames(deps)
        if len(filenames) == 0:
            raise Exception("No %s files for bundle '%s'" %
                            (self.NAME, self.bundle.name))

        filename = self.props["out"]
        base = os.path.dirname(filename)
        if not os.path.isdir(base):
            os.makedirs(base, mode=0755)

        out = open(filename, "w")

        for f in filenames:
            out.write("%s\n" % self.get_file_comment(f))
            out.write(read_file(f))
            out.write("\n\n")
