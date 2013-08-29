from abc import ABCMeta, abstractproperty


class NodeException(Exception):
    __metaclass__ = ABCMeta

    def __init__(self, node):
        super(NodeException, self).__init__(
            "%s (<%s>, %s:%d:%d)" %
            (self.get_message(), node.tagName, node.filename, node.lineNo,
             node.colNo)
        )

    @abstractproperty
    def get_message(self):
        pass


class UnexpectedNodeException(NodeException):
    def get_message(self):
        return "Unexpected node"


class EmptyNodeException(NodeException):
    def get_message(self):
        return "Node is empty"


class NoNameNodeException(NodeException):
    def get_message(self):
        return "No name"


class CustomNodeException(NodeException):
    def __init__(self, node, msg):
        self._msg = msg
        super(CustomNodeException, self).__init__(node)

    def get_message(self):
        return self._msg


class UnknownTechNodeException(NodeException):
    def get_message(self):
        return "Unknown tech"


class UnsupportedScheme(Exception):
    def __init__(self, scheme, filename):
        super(UnsupportedScheme, self).__init__(
            "Unsupported scheme '%s' in '%s' filename" % (scheme, filename)
        )
