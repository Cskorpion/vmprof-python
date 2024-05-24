import os
import struct, pytest
from vmprof.reader import LogReader, LogReaderState, FdWrapper, VERSION_TIMESTAMP, VERSION_SAMPLE_TIMEOFFSET
from vmprof.test.test_run import  BufferTooSmallError, FileObjWrapper

class FileObj(object):
    def __init__(self, lst=None):
        self.s = b''
        if lst is None:
            return
        for item in lst:
            if isinstance(item, int):
                item = struct.pack('l', item)
            self.write(item)

    def read(self, count):
        if self.s:
            s = self.s[:count]
            self.s = self.s[count:]
            return s # might be incomplete
        return b''

    def write(self, s):
        self.s += s

    def tell(self):
        return 0

def test_fileobj():
    f = FileObj()
    f.write(b'foo')
    f.write(b'bar')
    assert f.read(2) == b'fo'
    assert f.read(2) == b'ob'
    assert f.read(4) == b'ar'
    assert f.read(1) == b''

def test_fileobj_wrapper():
    f1 = FileObj([b"123456"])
    fw = FileObjWrapper(f1)
    assert fw.read(4) == b"1234"
    exc = pytest.raises(BufferTooSmallError, fw.read, 4)
    f1.write(b"789")
    fw = FileObjWrapper(f1, exc.value.get_buf())
    assert fw.read(3) == b'123'
    assert fw.read(4) == b'4567'
    assert fw.read(2) == b'89'

def test_no_timestamps_read_count():
    path = os.path.dirname(os.path.abspath(__file__))
    file_path = path + "/cpuburn.cpython.prof"
    file = open(file_path) # find and open .prof file

    fileobj = FdWrapper(file.fileno())
    logreader = LogReader(fileobj, LogReaderState())
    logreader.read_all() # read profile
    file.close()

    state = logreader.state

    assert state.version <= VERSION_TIMESTAMP # VERSION_TIMESTAMP and prior versions do not support sample timestamps

    assert type(state.profiles[0][1]) == int # timestamps are float
    assert state.profiles[0][1] == 1
    #...
    assert type(state.profiles[-1][1]) == int
    assert state.profiles[-1][1] == 1

    assert "start_time_offset" not in state.meta # profiling start time

def test_timestamps_read_offsets():
    path = os.path.dirname(os.path.abspath(__file__))
    file_path = path + "/cpuburn.cpython.tsprof"
    file = open(file_path) # find and open .prof file

    fileobj = FdWrapper(file.fileno())
    logreader = LogReader(fileobj, LogReaderState())
    logreader.read_all() # read profile
    file.close()

    state = logreader.state

    assert state.version == VERSION_SAMPLE_TIMEOFFSET # This version supports sample timestamps

    assert type(state.profiles[0][1]) == float # sample timestamps are float
    assert state.profiles[0][1] == 451.370060965 # secs from CLOCK_MONOTONIC
    #...
    assert type(state.profiles[-1][1]) == float
    assert state.profiles[-1][1] == 481.790013875

    assert "start_time_offset" in state.meta
    # profiling start time (recorded immediately after MARKER_TIME_N_ZONE start unix timestamp)
    assert state.meta["start_time_offset"] == "451.359228"

