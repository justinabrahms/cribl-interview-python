from functools import lru_cache
from fastapi import FastAPI, Response, status, Depends, Query
from typing import Union, Annotated, Callable
from typing.io import TextIO
import os
from pydantic_settings import BaseSettings
import os.path
import itertools

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
        keywords: Annotated[Union[list[str], None], Query()] = None
):
    normalized_path = os.path.abspath(os.path.join(settings.root_directory, relative_path))

    max_results = min(
        # Convince the type checker that this is valid.
        max_results or settings.max_results,
        settings.max_results
    )


    print({'relative': relative_path, 'absolute': normalized_path, 'results': max_results, 'keywords': keywords})

    try:
        lines = get_relevant_lines_from_file(normalized_path, max_results, keywords)

    except OSError:
        response.status_code = status.HTTP_404_NOT_FOUND
        return


    return {
        "lines": lines,
    }

def read_file_in_reverse(f: TextIO, chunk_size:int=1000):
    """Yield lines in reverse order, reading [chunk_size] portions at a time to
    reduce memory footprint. """
    if chunk_size <= 4:
        print("The chunk size is too small. This means that we cannot support all multi-byte utf-8 characters.")

    current_chunk = ""
    file_size = current_position = f.seek(0, os.SEEK_END)
    while current_position > 0:
        # We can only seek relative to the start of the file for text files, so
        # keep a running count by making it relative to the old
        # current_position.
        # import pdb; pdb.set_trace()
        seek_to = max(current_position-chunk_size, 0)
        current_position = f.seek(seek_to)
        # exit if current_position == 0?
        nearer_to_top_of_file = f.read(chunk_size)

        # Some bytes in utf-8 are "continuation bytes" which mean we've sliced
        # something mid-character. The "don't split here" bytes begin with
        # b'10', so that puts 0x80 and 0xc0 as the upper and lower bounds
        # (inclusive). If this happens, adjust our seek window appropriately and
        # re-read.
        #
        # More details at https://en.wikipedia.org/wiki/UTF-8#Encoding_process
        bytes_to_offset = 0
        while len(nearer_to_top_of_file) > 0 and nearer_to_top_of_file[0] >= 0x80 and nearer_to_top_of_file[0] <= 0xc0:
            bytes_to_offset += 1
            nearer_to_top_of_file = nearer_to_top_of_file[1:]

        if bytes_to_offset > 0:
            current_position += bytes_to_offset
            f.seek(seek_to+bytes_to_offset)

        current_chunk = nearer_to_top_of_file.decode('utf-8') + current_chunk
        lines = current_chunk.splitlines()
        leftover = lines[0]
        for to_yield in reversed(lines[1:]):
            yield to_yield
            current_chunk = leftover
    # Get what's dangling, which will be the final line at the top.
    yield current_chunk

KWTree = dict[str, Union['KWTree', bool]]

def keywords_to_tree(keywords: list[str]) -> KWTree:
    """
    Convert a list of keywords to a tree structure with one character per
    level. This will allow us to make one pass through each line, looking for a
    match
    """
    tree: KWTree = {}

    # TODO: We could optimize this by making the structure handle word stems, so
    # instead of one character per level, we have unique substrings at each
    # level for the given set of keywords.
    for keyword in keywords:
        current_branch = tree
        kw_len = len(keyword)
        for i, char in enumerate(keyword):
            if char not in current_branch:
                current_branch[char] = {}
            if i+1 == kw_len:
                # ending of keyword
                current_branch[char]['terminal'] = True
            else:
                current_branch = current_branch[char]
    return tree

def contains_keywords(keyword_tree: KWTree) -> Callable[[str], bool]:
    """
    Returns a function suitable for calling filter() on, which returns True if a
    line matches one of the keywords.
    """
    def check(line: str) -> bool:
        in_progress: list[KWTree] = []
        for char in line:
            # If we've reached a terminal node, we've matched.

            if keyword_tree.get(char, {}).get('terminal', False):
                return True

            # Check for in-progress matches. Keep a running list of "found"
            # stems to look through next time.
            keep_looking_for = []
            for entry in in_progress:
                if char in entry:
                    if entry[char].get('terminal'):
                        return True
                    keep_looking_for.append(entry[char])
            in_progress = keep_looking_for

            if keyword_tree.get(char):
                in_progress.append(keyword_tree[char])
        return False

    return check


# Main logic, devoid of HTTP semantics, which makes this easier to test or benchmark.
def get_relevant_lines_from_file(path: str | os.PathLike, max_results: int, keywords: list[str]) -> list[str]:
    with open(path, 'rb') as f:
        # Note, we need to consume the generator while the file is still opened.
        line_generator = read_file_in_reverse(f)
        if keywords is not None and len(keywords) != 0:
            kw_tree = keywords_to_tree(keywords)
            line_generator = filter(contains_keywords(kw_tree), line_generator)

        return list(itertools.islice(line_generator, max_results))
