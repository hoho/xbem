from xbem.tech import BuildTech, BundleBuildTech


class XSLBuildTech(BuildTech):
    pass


class XSLBundleBuildTech(BundleBuildTech):
    NAME = "xsl"

    def build(self, deps):
        pass
