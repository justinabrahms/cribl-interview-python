import io
from cribl_python_interview.main import read_file_in_reverse
import os.path

def test_simple_file():
    f = io.BytesIO(b"line1\nline2")
    result = read_file_in_reverse(f)
    assert list(result) == ["line2", "line1"]

def test_utf8():
    with open(os.path.join(os.path.dirname(__file__), 'UTF-8-demo.txt'), 'rb') as f:
        assert next(read_file_in_reverse(f, chunk_size=20)) != ""
