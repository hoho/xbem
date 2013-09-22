from xbem.decl import DependencyBlock


class Dependencies(object):
    def __init__(self, repo):
        self.repo = repo
        self._deps = []
        self._deps_set = set()
        self._deps_processed = set()

    def __add__(self, other):
        if len(self._deps) == 0:
            merged_deps = other._deps[:]
        elif len(other._deps) == 0:
            merged_deps = self._deps[:]
        else:
            merged_deps = []

            deps_map = {}
            for i in xrange(len(other._deps)):
                deps_map[other._deps[i].file] = i

            i = 0
            for dep in self._deps:
                j = deps_map.get(dep.file)
                if j is not None:
                    merged_deps += other._deps[i:j]
                    i = j + 1
                merged_deps.append(dep)

            if i < len(other._deps):
                merged_deps += other._deps[i:]

        ret = Dependencies(self.repo)
        ret._deps = merged_deps
        ret._deps_set = self._deps_set.union(other._deps_set)
        ret._deps_processed = self._deps_set.union(other._deps_processed)

        return ret

    def append(self, block_name, elem_name=None, modifier=None, value=None):
        self._append(block_name, elem_name, modifier, value, None)

    def _append(self, block_name, elem_name, modifier, value, start):
        if start is not None and block_name == start:
            raise Exception("Found dependency cycle in block '%s'" % start)

        if start is None:
            start = block_name

        key = (block_name, elem_name, modifier, value)

        if key in self._deps_processed:
            return

        block = self.repo.get_block(block_name)

        if block is None:
            raise Exception("Unknown block '%s'" % block_name)

        for dep in block.deps:
            self._append_by_dep(dep, start)

        self._append_files(block.files)

        if elem_name is None:
            if modifier is not None:
                mod_decls = filter(lambda x: x.name == modifier, block.mods)

                if len(mod_decls) == 0:
                    raise Exception("Unknown modifier '%s' of block '%s'" %
                                    (modifier, block_name))

                for m in mod_decls:
                    if m.value is None or m.value == value:
                        self._append_files(m.files)
        else:
            elem_decls = filter(lambda x: x.name == elem_name, block.elements)

            if len(elem_decls) == 0:
                raise Exception("Unknown element '%s' of block '%s'" %
                                (elem_name, block_name))

            for e in elem_decls:
                self._append_files(e.files)

            if modifier is not None:
                mod_decls = []

                for e in elem_decls:
                    mod_decls += filter(lambda x: x.name == modifier, e.mods)

                if len(mod_decls) == 0:
                    raise Exception("Unknown modifier '%s' of element '%s' of"
                                    " block '%s'" %
                                    (modifier, elem_name, block_name))

                for m in mod_decls:
                    if m.value is None or m.value == value:
                        self._append_files(m.files)

        self._deps_processed.add(key)

    def _append_files(self, files):
        for f in files:
            if not f in self._deps_set:
                self._deps.append(f)
                self._deps_set.add(f)

    def _append_by_dep(self, dep, start):
        if not isinstance(dep, DependencyBlock):
            raise Exception("First argument should be an instance of "
                            "DependencyBlock()")
        self._append(dep.name, None, None, None, start)

        for mod in dep.modifiers:
            self._append(dep.name, None, mod.name, mod.value, start)

        for elem in dep.elements:
            self._append(dep.name, elem.name, None, None, start)

            for mod in elem.modifiers:
                self._append(dep.name, elem.name, mod.name, mod.value, start)

    def get_filenames(self, file_type, bundle=None):
        files_set = set()

        return map(
            lambda x: x.file,
            filter(
                lambda x:
                    x.file not in files_set and
                    not files_set.add(x.file) and
                    x.type == file_type and
                    (bundle is None or x.bundle == bundle),
                self._deps
            )
        )
