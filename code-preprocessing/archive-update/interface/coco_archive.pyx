# cython: language_level=3
"""Bindings to the COCO bi-objective archive in the generated C core."""

cdef extern from "coco.h":
    ctypedef struct coco_archive_t:
        pass

    coco_archive_t *coco_archive(const char *suite_name, size_t function,
                                 size_t dimension, size_t instance)
    int coco_archive_add_solution(coco_archive_t *archive, double f1, double f2, const char *text)
    size_t coco_archive_get_number_of_solutions(coco_archive_t *archive)
    double coco_archive_get_hypervolume(coco_archive_t *archive)
    const char *coco_archive_get_next_solution_text(coco_archive_t *archive)
    void coco_archive_free(coco_archive_t *archive)

    const char *coco_set_log_level(const char *level)


cdef bytes _bstring(s):
    if isinstance(s, bytes):
        return s
    elif isinstance(s, str):
        return s.encode('ascii')
    else:
        raise TypeError("expected bytes or ASCII str")


cdef class Archive:
    """C-backed bi-objective archive (same Python API as the original cocoprep)."""
    cdef coco_archive_t *archive
    cdef bytes _suite_name
    cdef size_t _function
    cdef size_t _dimension
    cdef size_t _instance
    cdef size_t _number_of_solutions
    cdef double _hypervolume
    cdef bytes _tmp_text
    cdef bint up_to_date

    def __cinit__(self, suite_name, function, instance, dimension):
        self.archive = NULL
        # COCO's extended biobjective suite shares the bbob-biobj filename stem.
        if suite_name == 'bbob-biobj' and 56 <= function <= 92:
            self._suite_name = _bstring('bbob-biobj-ext')
        else:
            self._suite_name = _bstring(suite_name)
        self._function = function
        self._instance = instance
        self._dimension = dimension
        self.up_to_date = False
        self.archive = coco_archive(self._suite_name, self._function,
                                    self._dimension, self._instance)
        if self.archive == NULL:
            raise MemoryError("COCO could not create the archive")

    def __dealloc__(self):
        if self.archive != NULL:
            coco_archive_free(self.archive)

    def add_solution(self, f1, f2, text):
        updated = coco_archive_add_solution(self.archive, f1, f2, _bstring(text))
        if updated:
            self.up_to_date = False
        return updated

    def get_next_solution_text(self):
        cdef const char *value = coco_archive_get_next_solution_text(self.archive)
        if value == NULL or value[0] == 0:
            return None
        self._tmp_text = value
        return self._tmp_text.decode('ascii')

    def update(self):
        if not self.up_to_date:
            self._number_of_solutions = coco_archive_get_number_of_solutions(self.archive)
            self._hypervolume = coco_archive_get_hypervolume(self.archive)
            self.up_to_date = True

    @property
    def number_of_solutions(self):
        self.update()
        return self._number_of_solutions

    @property
    def hypervolume(self):
        self.update()
        return self._hypervolume


def log_level(level=None):
    """Get the current COCO log level and optionally change it."""
    cdef bytes _level = _bstring(level if level is not None else "")
    cdef const char *old_level = coco_set_log_level(_level)
    if old_level == NULL:
        return None
    return (<bytes>old_level).decode('ascii')
