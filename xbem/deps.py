from xbem.decl import Dependency


class Dependencies(object):
    def __init__(self):
        pass

    def __add__(self, other):
        return self

    def append(self, dep):
        if not isinstance(dep, Dependency):
            raise Exception("First argument should be an instance of "
                            "Dependency()")
        pass

    def get_filenames(self, file_type):
        pass
