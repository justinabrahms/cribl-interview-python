from cribl_python_interview.main import app, get_settings, Settings
from fastapi.testclient import TestClient

client = TestClient(app)

def settings_override():
    return Settings(root_directory="./../") # not relative to test directory

app.dependency_overrides[get_settings] = settings_override

def test_nonexistent_file():
    response = client.get("/logs/foo")
    assert response.status_code == 404


def test_read_a_few():
    response = client.get("/logs/question.md?max_results=1")
    assert response.status_code == 200
    assert response.json() == {
        "lines": ["used between the primary and secondary servers, and the architecture is completely up to you."]
    }
