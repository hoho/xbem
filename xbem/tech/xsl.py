from os import path

from xbem.tools import parse_xml, create_subdirectories
from xbem.ns import XBEM_BLOCK_NAMESPACE
from xbem.tech import (BuildTech,
                       BundleBuildTech,
                       XMLDependenciesExtractor,
                       PROPERTY_EXISTING_FILE,
                       PROPERTY_NEW_FILE_OR_DIRECTORY)

XSLT_NAMESPACE = "http://www.w3.org/1999/XSL/Transform"


class XSLDependenciesExtractor(XMLDependenciesExtractor):
    def other(self, node, namespaces):
        if node.namespaceURI == XSLT_NAMESPACE:
            if node.localName in ("import", "include") and not self.no_imports:
                filename = node.filename
                href = node.getAttribute("href")
                href = path.normpath(path.join(path.dirname(filename), href))
                xsl = parse_xml(href)
                self.extract(xsl.firstChild)
            elif node.localName == "call-template":
                name = node.getAttribute("name").strip()
                i = name.find(":")
                if i > 0:
                    prefix = name[:i]
                    prefixes = namespaces.get(XBEM_BLOCK_NAMESPACE)
                    if prefixes is not None and prefix in prefixes:
                        self.deps.append(name[i + 1:])


class XSLSaveWithImports(object):
    def __init__(self, repo, filename, out):
        self.repo = repo
        self.filename = filename
        self.out = out
        self._number = -1
        doc = parse_xml(filename, remove_blank_nodes=False)
        self.insert_deps(doc)
        self.fix_imports(doc.firstChild)
        create_subdirectories(out, is_filename=True)
        f = open(out, "w")
        f.write(doc.toxml(encoding="utf-8"))
        f.close()

    def insert_deps(self, doc):
        e = XSLDependenciesExtractor(self.repo, doc.firstChild, True)
        deps = e.get_deps()
        for filename in deps.get_filenames("xsl")[::-1]:
            ie = doc.createElementNS(XSLT_NAMESPACE, "import")
            ie.setAttribute("href", filename)
            doc.firstChild.insertBefore(ie, doc.firstChild.firstChild)

    def fix_import(self, node):
        if node.namespaceURI == XSLT_NAMESPACE and \
           node.localName in ("import", "include"):
            href = self.get_import_abspath(node.getAttribute("href"))
            newhref = self.get_next_filename()
            node.setAttribute("href", newhref)
            XSLSaveWithImports(self.repo, href, newhref)
            return True
        else:
            return False

    def get_next_filename(self):
        self._number += 1
        return "%s_%s" % (self.out, self._number)

    def get_import_abspath(self, filename):
        return path.normpath(path.join(path.dirname(self.filename), filename))

    def fix_imports(self, node):
        if not self.fix_import(node):
            node = node.firstChild
            while node is not None:
                self.fix_imports(node)
                node = node.nextSibling


class XSLBuildTech(BuildTech):
    NAME = "xsl"
    PROPERTIES = {
        "file": PROPERTY_EXISTING_FILE,
        "out": PROPERTY_NEW_FILE_OR_DIRECTORY
    }

    def get_deps(self, repo):
        xsl = parse_xml(self.props["file"])
        extractor = XSLDependenciesExtractor(repo, xsl.firstChild)
        return extractor.get_deps()

    def build(self, deps, repo):
        XSLSaveWithImports(self.props["file"], self.props["out"])


class XSLBundleBuildTech(BundleBuildTech):
    NAME = "xsl"

    def build(self, deps, repo):
        pass
