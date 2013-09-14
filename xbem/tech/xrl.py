from os import path

from xbem.tools import parse_xml, create_subdirectories
from xbem.tech.xsl import XSLSaveWithImports
from xbem.tech import (BuildTech,
                       XMLDependenciesExtractor,
                       PROPERTY_EXISTING_FILE,
                       PROPERTY_DIRECTORY,
                       PROPERTY_NEW_FILE_OR_DIRECTORY)

XRLT_NAMESPACE = "http://xrlt.net/Transform"


class XRLSaveWithImports(XSLSaveWithImports):
    def __init__(self, repo, deps, filename, out, templates):
        self.templates = templates
        self._xslnumber = -1
        create_subdirectories(templates, is_filename=False)
        super(XRLSaveWithImports, self).__init__(repo, deps, filename, out)

    def insert_deps(self, doc):
        return

    def fix_import(self, node):
        if node.namespaceURI == XRLT_NAMESPACE:
            if node.localName == "import":
                href = self.get_import_abspath(node.getAttribute("href"))
                newhref = self.get_next_filename()
                node.setAttribute("href", newhref)
                XRLSaveWithImports(self.repo, self.deps, href, newhref,
                                   self.templates)
                return True
            elif node.localName == "transformation" and \
                 node.hasAttribute("src"):
                src = self.get_import_abspath(node.getAttribute("src"))
                newsrc = self.get_next_filename(True)
                node.setAttribute("src", newsrc)
                XSLSaveWithImports(self.repo, self.deps, src, newsrc)
                return True
        return False

    def get_next_filename(self, is_xsl=False):
        if not is_xsl:
            return super(XRLSaveWithImports, self).get_next_filename()
        else:
            self._xslnumber += 1
            return "%s.xsl_%s" % (
                path.normpath(path.join(self.templates,
                                        path.basename(self.filename))),
                self._xslnumber
            )


class XRLDependenciesExtractor(XMLDependenciesExtractor):
    def other(self, node, namespaces):
        if node.namespaceURI == XRLT_NAMESPACE and node.localName == "import":
            filename = node.filename
            href = node.getAttribute("href")
            href = path.normpath(path.join(path.dirname(filename), href))
            xml = parse_xml(href)
            self.extract(xml.firstChild)


class XRLBuildTech(BuildTech):
    NAME = "xrl"
    PROPERTIES = {
        "file": PROPERTY_EXISTING_FILE,
        "templates": PROPERTY_DIRECTORY,
        "out": PROPERTY_NEW_FILE_OR_DIRECTORY
    }

    def get_deps(self, repo):
        xrl = parse_xml(self.props["file"])
        extractor = XRLDependenciesExtractor(repo, xrl.firstChild)
        return extractor.get_deps()

    def build(self, deps, repo):
        XRLSaveWithImports(repo, deps, self.props["file"], self.props["out"],
                           self.props["templates"])
