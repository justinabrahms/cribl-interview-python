# Log file viewer

Supports reading log files from a given directory, as well as basic keyword search.

## Examples

```bash
# Return the last 10 lines of $ROOT_DIRECTORY/big-text-file.txt
$ curl -v http://localhost:8000/logs/big-text-file.txt?max_results=10
{
 "lines": ["..."]
}

# Return the last 10 lines of $ROOT_DIRECTORY/myfile.txt that match "test" or "foo"
$ curl -v http://localhost:8000/logs/myfile.txt?keywords=test&keywords=foo
{
 "lines": ["..."]
}
```

## Running the system
```sh
pipx install poetry
poetry run uvicorn cribl_python_interview.main:app --reload
```

Environment variables you can use to change behavior:
- `ROOT_DIRECTORY`: Where to serve content from. Note that callers can read any file under this, so careful to leaking secrets. (e.g. don't use `/`). Defaults to `.`
- `MAX_RESULTS`: How many results should someone be allowed to request?

## Development

Running tests:
```sh
poetry run pytest -vv
```
