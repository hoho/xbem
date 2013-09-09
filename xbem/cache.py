import urlparse


class Cache(object):
    _caches = {}

    def __new__(cls, path):
        self = cls._caches.get(path)
        if self is None:
            cls._caches[path] = self = super(Cache, cls).__new__(cls)
            self.path = path
            self._cache = {}
        return self

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
