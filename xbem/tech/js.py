from xbem.tech import ConcatFilesBundleBuildTech


class JSBundleBuildTech(ConcatFilesBundleBuildTech):
    NAME = "js"

    def get_file_comment(self, filename):
        return "/* %s */\n" % filename
