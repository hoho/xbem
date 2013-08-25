from abc import ABCMeta, abstractmethod, abstractproperty
from xbem import *
from xbem.exceptions import *
from xbem.xmltools import get_node_text
import os

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

        print self.props

    @abstractmethod
    def build(self, deps):
        pass


class BuildTech(AbstractBuildTech):
    @abstractproperty
    def get_deps(self, blocks_paths):
        pass


class XRLBuildTech(BuildTech):
    NAME = "xrl"
    PROPERTIES = {
        "file": PROPERTY_EXISTING_FILE,
        "templates": PROPERTY_DIRECTORY,
        "out": PROPERTY_NEW_FILE_OR_DIRECTORY
    }

    def get_deps(self, blocks_paths):
        pass

    def build(self, deps):
        pass


class XSLBuildTech(BuildTech):
    pass


class BundleBuildTech(AbstractBuildTech):
    PROPERTIES = {
        "out": PROPERTY_NEW_FILE_OR_DIRECTORY,
        "rel": PROPERTY_STRING
    }


class CSSBundleBuildTech(BundleBuildTech):
    NAME = "css"

    def build(self, deps):
        pass


class JSBundleBuildTech(BundleBuildTech):
    NAME = "js"

    def build(self, deps):
        pass


class ImageBundleBuildTech(BundleBuildTech):
    NAME = "image"

    def build(self, deps):
        pass


class XSLBundleBuildTech(BundleBuildTech):
    NAME = "xsl"

    def build(self, deps):
        pass
