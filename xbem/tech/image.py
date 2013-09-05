import os

from xbem.tech import BundleBuildTech
from xbem.tools import read_file


class ImageBundleBuildTech(BundleBuildTech):
    NAME = "image"

    def build(self, deps, blocks_repos):
        filenames = self.get_filenames(deps)
        if len(filenames) == 0:
            raise Exception("No %s files for bundle '%s'" %
                            (self.NAME, self.bundle.name))

        base = self.props["out"]
        if not os.path.isdir(base):
            os.makedirs(base, mode=0755)

        for f in filenames:
            read_file(f, os.path.join(base, os.path.basename(f)))
