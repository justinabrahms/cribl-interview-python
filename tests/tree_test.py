from cribl_python_interview.main import keywords_to_tree, contains_keywords

def test_empty():
    assert {} == keywords_to_tree([])

def test_separate():
    tree = keywords_to_tree(['cat', 'bat'])
    assert tree == {
        'c': {
            'a': {
                't': {
                    'terminal': True,
                },
            },
        },
        'b': {
            'a': {
                't': {
                    'terminal': True
                }
            }
        }
    }

def test_similar():
    tree = keywords_to_tree(['cat', 'car'])
    assert tree == {
        'c': {
            'a': {
                't': {
                    'terminal': True,
                },
                'r': {
                    'terminal': True,
                }
            },
        },
    }

def test_keyword_not_contains():
    lines = ["test"]
    results = list(filter(contains_keywords(keywords_to_tree(["nope"])), lines))
    assert results == []

def test_single_char():
    lines = ["test"]
    results = list(filter(contains_keywords(keywords_to_tree(["t"])), lines))
    assert results == ["test"]

def test_multi_char():
    lines = ["testing"]
    results = list(filter(contains_keywords(keywords_to_tree(["test"])), lines))
    assert results == ["testing"]

def test_duplicated_char():
    lines = ["batter"]
    results = list(filter(contains_keywords(keywords_to_tree(["ter"])), lines))
    assert results == ["batter"]
