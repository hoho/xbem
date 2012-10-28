import os
from sys import argv
from ConfigParser import ConfigParser
import shlex
from glob import glob
from lxml import etree
from copy import deepcopy

from xbem_build.builders import init_builder


class SetupException(Exception):
    pass


class BuildSettings(object):
    def __init__(self, name):
        self.NAME = name
        self.BLOCKS = None
        self.PAGES = None
        self.DEPS_COMMON = []
        self.BUILD = None
        self.BUILDERS = []
        self.BUILDERS_COMMON = []

    def feed(self, optname, value):
        if optname == "blocks":
            if not value:
                raise SetupException("Blocks are not supplied")
            blocks = shlex.split(value)
            ret = []
            for b in blocks:
                b = os.path.normpath(os.path.abspath(b))
                if not os.path.isdir(b):
                    raise SetupException("'%s' is not a directory" % b)
                ret.append(os.path.relpath(b))
            self.BLOCKS = ret
        elif optname == "pages":
            if not value:
                raise SetupException("Pages are not supplied")
            pages = shlex.split(value)
            page_paths = {}
            for p in pages:
                for p in glob(p):
                    p = os.path.normpath(os.path.abspath(p))
                    if not os.path.isfile(p):
                        raise SetupException("'%s' is not a file" % p)
                    page_paths[os.path.relpath(p)] = True
            self.PAGES = page_paths.keys()
        elif optname == "deps_common":
            self.DEPS_COMMON = shlex.split(value)
        elif optname == "build":
            if not value:
                raise SetupException("Build directory is not supplied")
            build = shlex.split(value)
            if len(build) > 1:
                raise SetupException("Only single build directory is "
                                     "supported")
            elif build:
                self.BUILD = os.path.normpath(build[0])
        elif optname.startswith("build_common_"):
            builder = init_builder(optname[13:], value, True)
            self.BUILDERS_COMMON.append(builder)
        elif optname.startswith("build_"):
            builder = init_builder(optname[6:], value, False)
            self.BUILDERS.append(builder)
        else:
            raise SetupException("Unknown option name: '%s'" % optname)

    def test(self):
        if not self.BLOCKS:
            raise SetupException("Blocks are not supplied")
        if not self.PAGES:
            raise SetupException("Pages are not supplied")
        if not self.BUILD:
            raise SetupException("Build directory is not supplied")
        return True


class XBEM(object):
    NAMESPACES = {"block": "http://xslc.org/XBEM/Block",
                  "elem": "http://xslc.org/XBEM/Element",
                  "mod": "http://xslc.org/XBEM/Modifier",
                  "decl": "http://xslc.org/XBEM/Declaration"}
    def __init__(self, filename):
        self.xml = etree.parse(filename)
        self._blocks = None
        self._deps = None

    def get_blocks(self):
        if self._blocks is None:
            blocks = self.xml.xpath("//block:*", namespaces=self.NAMESPACES)
            self._blocks = []
            for b in blocks:
                self._blocks.append({
                    "name": b.xpath("local-name()"),
                    "mods": self.get_modifiers(b),
                    "elem": self.get_elements(b)
                })
        return self._blocks

    def get_modifiers(self, node):
        prefix = "{%s}" % self.NAMESPACES["mod"]
        ret = []
        for key, value in node.attrib.iteritems():
            if key.startswith(prefix):
                ret.append((key[len(prefix):], value))
        return ret

    def get_elements(self, node):
        ret = []
        n = deepcopy(node)
        subblocks = n.xpath(".//block:*", namespaces=self.NAMESPACES)
        for b in subblocks:
            b.getparent().remove(b)
        elems = n.xpath(".//elem:*", namespaces=self.NAMESPACES)
        for e in elems:
            ret.append({
                "name": e.xpath("local-name()"),
                "mods": self.get_modifiers(e)
            })
        return ret

    def get_dependencies(self):
        if self._deps is None:
            ret = []
            is_unique = {}
            blocks = self.get_blocks()
            for b in blocks:
                block = b["name"]
                # b-block/b-block
                d = "%s/%s" % (block, block)
                if not d in is_unique:
                    is_unique[d] = True
                    ret.append(d)
                for m in b["mods"]:
                    # b-block/b-block_mod_val
                    d = "%s/%s_%s_%s" % (block, block, m[0], m[1])
                    if not d in is_unique:
                        is_unique[d] = True
                        ret.append(d)
                    # b-block/_mod/b-block_mod_val
                    d = "%s/_%s/%s_%s_%s" % (block, m[0], block, m[0], m[1])
                    if not d in is_unique:
                        is_unique[d] = True
                        ret.append(d)
                for e in b["elem"]:
                    elem = e["name"]
                    # b-block/b-block__elem
                    d = "%s/%s__%s" % (block, block, elem)
                    if not d in is_unique:
                        is_unique[d] = True
                        ret.append(d)
                    # b-block/elem/b-block__elem
                    d = "%s/%s/%s__%s" % (block, elem, block, elem)
                    if not d in is_unique:
                        is_unique[d] = True
                        ret.append(d)
                    for m in e["mods"]:
                        # b-block/b-block__elem_mod_val
                        d = "%s/%s__%s_%s_%s" % (block, block, elem,
                                                 m[0], m[1])
                        if not d in is_unique:
                            is_unique[d] = True
                            ret.append(d)
                        # b-block/elem/b-block__elem_mod_val
                        d = "%s/%s/%s__%s_%s_%s" % (block, elem, block, elem,
                                                    m[0], m[1])
                        if not d in is_unique:
                            is_unique[d] = True
                            ret.append(d)
                        # b-block/elem/_mod/b-block__elem_mod_val
                        d = "%s/%s/_%s/%s__%s_%s_%s" % \
                            (block, elem, m[0], block, elem, m[0], m[1])
                        if not d in is_unique:
                            is_unique[d] = True
                            ret.append(d)
            self._deps = ret
        return self._deps


def merge_dependencies(*args):
    ret = []
    is_unique = {}
    for deps in args:
        for dep in deps:
            if not dep in is_unique:
                is_unique[dep] = True
                ret.append(dep)
    return ret


def main():
    if len(argv) < 2:
        raise SetupException("Build configuration file is not supplied")
    config = argv[1]
    if not os.path.isfile(config):
        raise SetupException("'%s' configuration file does not exist" % config)
    cfgparser = ConfigParser(allow_no_value=True)
    cfgparser.readfp(open(config))
    to_build = []
    for section in cfgparser.sections():
        settings = BuildSettings(section)
        for optname, value in cfgparser.items(section):
            settings.feed(optname, value)
        if settings.test():
            to_build.append(settings)
    for settings in to_build:
        deps_common = [settings.DEPS_COMMON]
        for page in settings.PAGES:
            xbem = XBEM(page)
            deps = xbem.get_dependencies()
            deps_common.append(deps)
            deps = settings.DEPS_COMMON + deps
            for builder in settings.BUILDERS:
                builder(settings.BLOCKS, settings.BUILD, deps, page, xbem=xbem)
        deps = merge_dependencies(*deps_common)
        for builder in settings.BUILDERS_COMMON:
            builder(settings.BLOCKS, settings.BUILD, deps)
