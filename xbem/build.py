import os
import pkgutil
import inspect

from xbem.ns import *
from xbem.exceptions import *
from xbem.tools import parse_xml, get_node_text
from xbem.repo import Repository
import xbem.tech


REGISTERED_TECHS = {}
REGISTERED_BUNDLE_TECHS = {}


class BuildBundle(object):
    def __init__(self, node):
        if node.namespaceURI != XBEM_BUILD_NAMESPACE:
            raise UnexpectedNodeException(node)
        if node.localName != "bundle":
            raise UnexpectedNodeException(node)

        self.name = None
        self.techs = []
        self._tech_by_name = {}

        tmp = node.firstChild

        while tmp is not None:
            if tmp.namespaceURI != XBEM_BUILD_NAMESPACE:
                raise UnexpectedNodeException(tmp)

            if tmp.localName == "name":
                if self.name is None:
                    self.name = get_node_text(tmp)
                else:
                    raise UnexpectedNodeException(tmp)
            else:
                tech = REGISTERED_BUNDLE_TECHS.get(tmp.localName)
                if tech is None:
                    raise UnknownTechNodeException(tmp)
                tech_instance = tech(self, tmp)
                self.techs.append(tech_instance)
                self._tech_by_name[tech_instance.NAME] = tech

            tmp = tmp.nextSibling

        if self.name is None:
            raise NoNameNodeException(node)

    def build(self, deps):
        for tech in self.techs:
            tech.build(deps)

    def get_rel(self, tech_name):
        tech = self._tech_by_name.get(tech_name)
        if tech is not None:
            return tech.props.get("rel")


class BuildSection(object):
    def __init__(self, node, repo=None):
        if node.namespaceURI != XBEM_BUILD_NAMESPACE:
            raise UnexpectedNodeException(node)
        if node.localName != 'build':
            raise UnexpectedNodeException(node)

        self._deps = None
        self.repo = Repository(repo)
        self.subsections = []
        self.bundles = []
        self.techs = []

        node = node.firstChild

        while node is not None:
            if node.namespaceURI != XBEM_BUILD_NAMESPACE:
                raise UnexpectedNodeException(node)

            if node.localName == "repository":
                self.repo.add_source(get_node_text(node))
            elif node.localName == "build":
                self.subsections.append(BuildSection(node, self.repo))
            elif node.localName == "bundle":
                self.bundles.append(BuildBundle(node))
            else:
                tech = REGISTERED_TECHS.get(node.localName)
                if tech is None:
                    raise UnknownTechNodeException(node)
                self.techs.append(tech(node))

            node = node.nextSibling

    def build(self):
        for subsection in self.subsections:
            subsection.build()
            self.add_deps(subsection.get_deps())

        for tech in self.techs:
            deps = tech.get_deps(self.repo)
            tech.build(deps)
            self.add_deps(deps)

        for bundle in self.bundles:
            bundle.build(self.get_deps())

    def add_deps(self, deps):
        if self._deps is None:
            self._deps = deps
        elif deps is not None:
            self._deps += deps

    def get_deps(self):
        return self._deps


def build(filename):
    cwd = os.getcwd()
    base = os.path.dirname(os.path.abspath(filename))
    os.chdir(base)
    build_config = parse_xml(filename)
    build = BuildSection(build_config.firstChild)
    build.build()
    os.chdir(cwd)
    raise


# Dynamically load technologies from xbem.tech.* submodules.
_tech_modules = pkgutil.iter_modules([os.path.dirname(xbem.tech.__file__)])

for _tech_loader, _name, _ in _tech_modules:
    _module = _tech_loader.find_module(_name).load_module(_name)

    _attr = filter(
        lambda x: inspect.isclass(x) and
                  issubclass(x, xbem.tech.AbstractBuildTech) and
                  x.NAME is not None,
        map(lambda x: getattr(_module, x), dir(_module))
    )

    for _tech_class in _attr:
        if issubclass(_tech_class, xbem.tech.BundleBuildTech):
            _tmp = REGISTERED_BUNDLE_TECHS.get(_tech_class.NAME)
            if _tmp is not None:
                raise Exception("'%s' bundle build tech is already "
                                "registered" % _tech_class.NAME)
            REGISTERED_BUNDLE_TECHS[_tech_class.NAME] = _tech_class
        else:
            _tmp = REGISTERED_TECHS.get(_tech_class.NAME)
            if _tmp is not None:
                raise Exception("'%s' build tech is already registered" %
                                _tech_class.NAME)
            REGISTERED_TECHS[_tech_class.NAME] = _tech_class
