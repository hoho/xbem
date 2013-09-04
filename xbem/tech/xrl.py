from xbem.tech import (BuildTech,
                       PROPERTY_EXISTING_FILE,
                       PROPERTY_DIRECTORY,
                       PROPERTY_NEW_FILE_OR_DIRECTORY)

from xbem.deps import Dependencies


class XRLBuildTech(BuildTech):
    NAME = "xrl"
    PROPERTIES = {
        "file": PROPERTY_EXISTING_FILE,
        "templates": PROPERTY_DIRECTORY,
        "out": PROPERTY_NEW_FILE_OR_DIRECTORY
    }

    def get_deps(self, blocks_repos):
        deps = Dependencies(blocks_repos)
        print blocks_repos
        deps.append("b-spinner")
        deps.append("b-cover")
        return deps

    def build(self, deps):
        pass
