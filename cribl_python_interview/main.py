from functools import lru_cache
from fastapi import FastAPI, Response, status, Depends
from typing import Union, Annotated
import os
from pydantic_settings import BaseSettings
import os.path

app = FastAPI()

class Settings(BaseSettings):
    root_directory: Union[str, os.PathLike] = "./"
    max_results: int = 100

# @lru_cache decorator makes it such that we don't regenerate a settings object
# on each request (which could be costly if we're reading from a file).
# Details: https://fastapi.tiangolo.com/advanced/settings/#creating-the-settings-only-once-with-lru_cache
@lru_cache
def get_settings():
    return Settings()


# NB: A useful feature of encoding the path in the url is that we exclude the
# possibility of path traversal attacks. Requesting /logs/../foo will translate
# into /foo which is an unknown route, rather than reading from e.g. /var/foo.
@app.get("/logs/{relative_path:path}", status_code=200)
def read_file(
        response: Response,
        settings: Annotated[Settings, Depends(get_settings)],
        relative_path: str,
        max_results: Union[int, None] = 10,
        keywords: Union[list[str], None] = None
):
    print("Relative path: ", relative_path)
    normalized_path = os.path.abspath(os.path.join(settings.root_directory, relative_path))
    max_results = min(max_results, settings.max_results)

    print("Normalized path: ", normalized_path)
    print("Max results: ", max_results)
    print("Keywords: ", keywords)

    try:
        with open(normalized_path) as f:
            reversed_lines = f.read().splitlines()[::-1]
    except OSError:
        response.status_code = status.HTTP_404_NOT_FOUND
        return


    return {
        "lines": reversed_lines[:max_results],
    }
