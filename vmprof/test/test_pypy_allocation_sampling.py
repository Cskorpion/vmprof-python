import sys
import vmprof
import pytest
import tempfile
from vmprof.profiler import read_profile

IS_PYPY = '__pypy__' in sys.builtin_module_names

def memory_hungry_func(size):
    l = []
    for i in range(size):
        l.append(2*32-1 - i)
    return l

# this test is only for pypy
def test_pypy_allocation_sampling():
    if not IS_PYPY:
        return
    tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".prof")

    vmprof.enable(tmpfile.fileno(), sample_n_bytes=64)

    l = memory_hungry_func(512) # 256 samples should be done here

    vmprof.disable()

    tmpfile.close()
    
    stats = read_profile(tmpfile.name)
    tree = stats.get_tree()

    assert tree.count >= 256 # there should be at least 256 samples
