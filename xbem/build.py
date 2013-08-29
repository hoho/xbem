import os

from xbem.ns import *
from xbem.exceptions import *
from xbem.tools import parse_xml, get_node_text
from xbem.tech import (XRLBuildTech, XSLBuildTech, CSSBundleBuildTech,
                       JSBundleBuildTech, ImageBundleBuildTech,
                       XSLBundleBuildTech)
from xbem.repo import Repository


REGISTERED_TECHS = {
    "xrl": XRLBuildTech,
    "xsl": XSLBuildTech
}

REGISTERED_BUNDLE_TECHS = {
    "css": CSSBundleBuildTech,
    "js": JSBundleBuildTech,
    "image": ImageBundleBuildTech,
    "xsl": XSLBundleBuildTech
}


class BuildBundle(object):
    def __init__(self, node):
        if node.namespaceURI != XBEM_BUILD_NAMESPACE:
            raise UnexpectedNodeException(node)
        if node.localName != "bundle":
            raise UnexpectedNodeException(node)

        self.name = None
        self.techs = []

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
                self.techs.append(tech(self, tmp))

            tmp = tmp.nextSibling

        if self.name is None:
            raise NoNameNodeException(node)

    def build(self, deps, rels):
        for tech in self.techs:
            tech.build(deps, rels)


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

            if node.localName == "blocks":
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

        rels = {}
        for bundle in self.bundles:
            for tech in bundle.techs:
                rel = tech.props.get("rel")
                if rel is not None:
                    rels["%s:%s" % (bundle.name, tech.NAME)] = rel

        for tech in self.techs:
            deps = tech.get_deps(self.repo)
            tech.build(deps, rels)
            self.add_deps(deps)

        for bundle in self.bundles:
            bundle.build(self.get_deps(), rels)

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
