import io
from cribl_python_interview.main import read_file_in_reverse

def test_simple_file():
    f = io.StringIO("line1\nline2")
    result = read_file_in_reverse(f)
    assert list(result) == ["line2", "line1"]

def test_utf8():
    f = io.StringIO("😀\n🫠")
    result = read_file_in_reverse(f, chunk_size=1)
    assert list(result) == ["🫠","😀"]
