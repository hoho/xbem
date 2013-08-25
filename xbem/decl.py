from xbem import *
from xbem.exceptions import *
from xbem.xmltools import get_node_text
from abc import ABCMeta, abstractproperty


class BlockFile(object):
    def __init__(self, node):
        if node.namespaceURI != XBEM_DECL_NAMESPACE:
            raise UnexpectedNodeException(node)

        self.type = node.localName
        self.file = None
        self.bundle = None

        node = node.firstChild

        while node is not None:
            if node.namespaceURI != XBEM_DECL_NAMESPACE:
                raise UnexpectedNodeException(node)
            if node.localName == "file":
                if self.file is None:
                    self.file = get_node_text(node)
                else:
                    raise UnexpectedNodeException(node)
            elif node.localName == "bundle":
                if self.bundle is None:
                    self.bundle = get_node_text(node)
                else:
                    raise UnexpectedNodeException(node)
            node = node.nextSibling

    def __repr__(self):
        return "BlockFile(file: '%s', type: '%s', bundle: '%s')" % \
               (self.file, self.type, self.bundle)


class Declaration(object):
    __metaclass__ = ABCMeta

    NAMESPACE = XBEM_DECL_NAMESPACE
    NAMESPACE2 = None
    LOCAL_NAME = None

    def __init__(self, node):
        self.name = None

        if node.namespaceURI != self.NAMESPACE:
            raise UnexpectedNodeException(node)
        if node.localName != self.LOCAL_NAME:
            raise UnexpectedNodeException(node)

        tmp = node.firstChild

        while tmp is not None:
            if tmp.namespaceURI is not None:
                if (tmp.namespaceURI == self.NAMESPACE and
                    not self.node_action(tmp)) \
                   or \
                   (tmp.namespaceURI == self.NAMESPACE2 and
                    not self.node_action2(tmp)):
                    raise UnexpectedNodeException(tmp)
            else:
                raise UnexpectedNodeException(tmp)
            tmp = tmp.nextSibling

        if self.name is None:
            raise NoNameNodeException(node)

    @abstractproperty
    def __repr__(self):
        pass

    def node_action(self, node):
        if node.localName == "name":
            if self.name is None:
                self.name = get_node_text(node)
                return True
            else:
                raise UnexpectedNodeException(node)
        else:
            return False

    def node_action2(self, node):
        return False


class Dependency(Declaration):
    pass


class DependencyModifier(Dependency):
    NAMESPACE = XBEM_DEP_NAMESPACE
    LOCAL_NAME = "modifier"

    def __init__(self, node):
        self.value = None
        super(DependencyModifier, self).__init__(node)

    def node_action(self, node):
        if not super(DependencyModifier, self).node_action(node):
            if node.localName == "value":
                if self.value is None:
                    self.value = get_node_text(node)
                    return True
                else:
                    raise UnexpectedNodeException(node)
            else:
                return False
        else:
            return True

    def __repr__(self):
        return "DependencyModifier(name: '%s', value: '%s')" % \
               (self.name, self.value or "")


class DependencyWithModifiers(Dependency):
    NAMESPACE = XBEM_DEP_NAMESPACE

    def __init__(self, node):
        self.modifiers = []
        super(DependencyWithModifiers, self).__init__(node)

    def node_action(self, node):
        if not super(DependencyWithModifiers, self).node_action(node):
            if node.localName == "modifier":
                self.modifiers.append(DependencyModifier(node))
                return True
            else:
                return False
        else:
            return True


class DependencyElement(DependencyWithModifiers):
    LOCAL_NAME = "element"

    def __repr__(self):
        return "DependencyElement(name: '%s', modifiers: %s)" % \
               (self.name, self.modifiers)


class DependencyBlock(DependencyWithModifiers):
    LOCAL_NAME = "block"

    def __init__(self, node):
        self.elements = []
        super(DependencyBlock, self).__init__(node)

    def __repr__(self):
        return "DependencyBlock(name: '%s', modifiers: %s, elements: %s" % \
               (self.name, self.modifiers, self.elements)

    def node_action(self, node):
        if not super(DependencyBlock, self).node_action(node):
            if node.localName == "element":
                self.elements.append(DependencyElement(node))
                return True
            else:
                return False
        else:
            return True


class DeclarationWithFilesAndDeps(Declaration):
    NAMESPACE2 = XBEM_DEP_NAMESPACE

    def __init__(self, node):
        self.files = []
        self.deps = []
        super(DeclarationWithFilesAndDeps, self).__init__(node)

    def node_action(self, node):
        if not super(DeclarationWithFilesAndDeps, self).node_action(node):
            if node.localName == "files":
                node = node.firstChild

                while node is not None:
                    self.files.append(BlockFile(node))
                    node = node.nextSibling

                return True
            else:
                return False
        else:
            return True

    def node_action2(self, node):
        self.deps.append(DependencyBlock(node))
        return True


class DeclarationModifier(DeclarationWithFilesAndDeps):
    LOCAL_NAME = "modifier"

    def __init__(self, node):
        self.value = None
        super(DeclarationModifier, self).__init__(node)

    def __repr__(self):
        return "DeclarationModifier(name: '%s', value: '%s', deps: %s, "     \
               "files: %s)" %                                                \
               (self.name, self.value or "", self.deps, self.files)

    def node_action(self, node):
        if not super(DeclarationModifier, self).node_action(node):
            if node.localName == "value":
                if self.value is None:
                    self.value = get_node_text(node)
                    return True
                else:
                    raise UnexpectedNodeException(node)
            else:
                return False
        else:
            return True


class DeclarationWithFilesDepsAndMods(DeclarationWithFilesAndDeps):
    def __init__(self, node):
        self.mods = []
        super(DeclarationWithFilesDepsAndMods, self).__init__(node)

    def node_action(self, node):
        if not super(DeclarationWithFilesDepsAndMods, self).node_action(node):
            if node.localName == "modifier":
                self.mods.append(DeclarationModifier(node))
                return True
            else:
                return False
        else:
            return True


class DeclarationElement(DeclarationWithFilesDepsAndMods):
    LOCAL_NAME = "element"

    def __repr__(self):
        return "DeclarationElement(name: '%s', modifiers: %s, deps: %s, "    \
               "files: %s)" %                                                \
               (self.name, self.mods, self.deps, self.files)


class DeclarationBlock(DeclarationWithFilesDepsAndMods):
    LOCAL_NAME = "block"

    def __init__(self, node):
        self.elements = []
        super(DeclarationBlock, self).__init__(node)

    def __repr__(self):
        return "DeclarationBlock(\n\t"                                       \
               "name: '%s'\n\t"                                              \
               "modifiers: %s,\n\t"                                          \
               "elements: %s,\n\t"                                           \
               "deps: %s,\n\t"                                               \
               "files: %s\n)" %                                              \
               (self.name, self.mods, self.elements, self.deps, self.files)

    def node_action(self, node):
        if not super(DeclarationBlock, self).node_action(node):
            if node.localName == "element":
                self.elements.append(DeclarationElement(node))
                return True
            else:
                return False
        else:
            return True
