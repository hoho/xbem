from xbem.tech import ConcatFilesBundleBuildTech


class CSSBundleBuildTech(ConcatFilesBundleBuildTech):
    NAME = "css"

    def get_file_comment(self, filename):
        return "/* %s */\n" % filename
