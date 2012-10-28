from abc import ABCMeta, abstractmethod, abstractproperty
import os
from lxml import etree
from sys import stdout
from ConfigParser import ConfigParser
import imp

BUILDERS = {}


class BuilderException(Exception):
    pass


def register_builder(name, cls):
    BUILDERS[name] = cls


def init_builder(name, value, is_common):
    builder = BUILDERS.get(name)
    if builder is None:
        raise BuilderException("'%s' builder is not registered" % name)
    return builder(value, is_common)


class BuildWhat(object):
    __metaclass__ = ABCMeta
    ALLOW_COMMON = False
    NAME = abstractproperty()

    def __init__(self, config_value, is_common):
        if is_common and not self.ALLOW_COMMON:
            raise BuilderException("'%s' builder can't be common" % self.NAME)
        self.config_value = config_value

    def get_files(self, blocks, deps, ext):
        ret = []
        is_unique = {}
        for dep in deps:
            for b in blocks:
                path = os.path.normpath(os.path.join(b, "%s.%s" % (dep, ext)))
                if not path in is_unique and os.path.isfile(path):
                    is_unique[path] = True
                    ret.append(path)
        return ret

    @abstractmethod
    def build(self, blocks, deps, relpath, xbem):
        pass

    @abstractmethod
    def get_filename(self, base):
        pass

    def __call__(self, blocks, build, deps, path=None, xbem=None):
        if path is None:
            path = self.config_value
        if path is None:
            raise BuilderException("No path to build to")
        path = os.path.normpath(os.path.join(build, path))
        dir = os.path.dirname(path)
        filename = os.path.basename(path)
        filename = filename.rsplit(".", 1)[0]
        path = os.path.join(dir, filename)
        try:
            os.makedirs(dir)
        except:
            pass
        relpath = "/".join([".." for x in dir.split("/") if x])
        filename = self.get_filename(path)
        stdout.write("Building %s..." % filename)
        f = open(filename, "w")
        f.write(self.build(blocks, deps, relpath, xbem))
        f.close()
        print " done."


class BuildXBEM(BuildWhat):
    NAME = "xbem"

    def get_filename(self, base):
        return "%s.xbem" % base

    def build(self, blocks, deps, relpath, xbem):
        if xbem is None:
            return
        if not hasattr(xbem, "built_xbem"):
            setattr(xbem, "built_xbem", True)
            files = self.get_files(blocks, deps, "build")
            for f in files:
                cfgparser = ConfigParser()
                cfgparser.readfp(open(f))
                section = os.path.basename(f)
                module = cfgparser.get(section, "module")
                func = cfgparser.get(section, "function")
                if module is None:
                    raise BuilderException(
                        "Module is not supplied in '%s'" % section)
                else:
                    module = module.rsplit(".", 1)[0]
                if func is None:
                    raise BuilderException(
                        "Function is not supplied in '%s'" % section)
                fp, pathname, description = imp.find_module(
                    module, [os.path.abspath(os.path.dirname(f))]
                )
                try:
                    module = imp.load_module(module, fp, pathname, description)
                    func = getattr(module, func)
                    func(xbem)
                finally:
                    # Since we may exit via an exception, close fp explicitly.
                    if fp:
                        fp.close()
        return etree.tostring(xbem.xml, pretty_print=True)


class BuildConcat(BuildXBEM):
    EXT = abstractproperty()

    def get_header(self):
        return ""

    def get_footer(self):
        return ""

    @abstractmethod
    def get_per_file_record(self, filename, relfilename):
        pass

    def get_filename(self, base):
        return "%s.%s" % (base, self.EXT)

    def build(self, blocks, deps, relpath, xbem):
        super(BuildConcat, self).build(blocks, deps, relpath, xbem)
        ret = []
        files = self.get_files(blocks, deps, self.EXT)
        if files:
            ret.append(self.get_header())
            for f in files:
                rf = os.path.normpath(os.path.join(relpath, f))
                ret.append(self.get_per_file_record(f, rf))
            ret.append(self.get_footer())
        ret = "\n".join(ret)
        return ret


class BuildXSL(BuildConcat):
    NAME = EXT = "xsl"

    def get_header(self):
        return "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n" \
               "<xsl:stylesheet " \
                   "xmlns:xsl=\"http://www.w3.org/1999/XSL/Transform\" " \
                   "version=\"1.0\">\n    "

    def get_footer(self):
        return "\n</xsl:stylesheet>"

    def get_per_file_record(self, filename, relfilename):
        return "<xsl:include href=\"%s\" />" % relfilename


class FileResolver(etree.Resolver):
    def resolve(self, url, pubid, context):
        return self.resolve_filename(url, context)


class BuildHTML(BuildXSL):
    NAME = "html"

    def get_filename(self, base):
        return "%s.html" % base

    def get_per_file_record(self, filename, relfilename):
        return "<xsl:include href=\"%s\" />" % filename

    def build(self, blocks, deps, relpath, xbem):
        xsl = super(BuildHTML, self).build(blocks, deps, relpath, xbem)
        parser = etree.XMLParser()
        parser.resolvers.add(FileResolver())
        xsl = etree.XML(xsl, parser)
        transform = etree.XSLT(xsl)
        return str(transform(xbem.xml))


class BuildJS(BuildConcat):
    ALLOW_COMMON = True
    NAME = EXT = "js"

    def get_per_file_record(self, filename, relfilename):
        return "\n/* Begin of %s. */\n%s\n/* End of %s. */\n" \
            % (relfilename, open(filename).read(), relfilename)


class BuildCSS(BuildConcat):
    ALLOW_COMMON = True
    NAME = EXT = "css"

    def get_per_file_record(self, filename, relfilename):
        return "\n/* Begin of %s. */\n%s\n/* End of %s. */\n" \
            % (relfilename, open(filename).read(), relfilename)


register_builder(BuildXBEM.NAME, BuildXBEM)
register_builder(BuildXSL.NAME, BuildXSL)
register_builder(BuildHTML.NAME, BuildHTML)
register_builder(BuildJS.NAME, BuildJS)
register_builder(BuildCSS.NAME, BuildCSS)
