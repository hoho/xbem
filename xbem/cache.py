import urlparse


class FileCache(object):
    _instance = None

    def __new__(cls, *args):
        if FileCache._instance is None:
            cls._instance = self = super(FileCache, cls).__new__(cls, *args)
            self._cache = {}
        return FileCache._instance

    def get_file_content(self, filename):
        cached = self._cache.get(filename)

        if cached is not None:
            pass
        else:
            url = urlparse.urlparse(filename)
            cached = None if url.scheme else filename
            self._cache[filename] = cached

        f = open(cached)
        ret = f.read()
        f.close()

        return ret
