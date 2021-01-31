import pytest

from tests.helpers import check
from yatl.types import YATLEnvironmentError, YATLSyntaxError


def test_for_as_object():
    test = """
        .for (x in xs): .(x)
    """
    expected = """
        - a
        - b
    """
    check(test, expected, {"xs": ["a", "b"]}, {})


def test_for_as_list():
    test = """
        - .for (x in xs): .(x)
    """
    expected = """
        - a
        - b
    """
    check(test, expected, {"xs": ["a", "b"]}, {})


def test_empty_for():
    test = """
        - .for (x in xs): .(x)
    """
    expected = """
        []
    """
    check(test, expected, {"xs": []}, {})


def test_extend_for():
    test = """
        - first
        - .for (x in xs): .(x)
    """
    expected = """
        - first
        - a
        - b
    """
    check(test, expected, {"xs": ["a", "b"]}, {})


def test_override_for():
    test = """
        - .(x)
        - .for (x in xs): .(x)
        - .(x)
    """
    expected = """
        - old
        - a
        - b
        - old
    """
    check(test, expected, {"x": "old", "xs": ["a", "b"]}, {})


def test_for_missing_variable():
    test = """
        - .for (x in xs): .(x)
    """
    with pytest.raises(YATLEnvironmentError):
        check(test, "", {}, {})


def test_for_variable_disappears():
    test = """
        - .for (x in xs): .(x)
        - .(x)
    """
    with pytest.raises(YATLEnvironmentError):
        check(test, "", {"xs": ["a", "b"]}, {})


def test_nested_for():
    test = """
        - .for (x in xs):
            - .for (y in ys): .(x).(y)
    """
    expected = """
        - ["a1", "a2"]
        - ["b1", "b2"]
    """
    check(test, expected, {"xs": ["a", "b"], "ys": [1, 2]}, {})


def test_for_not_only_key():
    test = """
        foo: bar
        .for (x in xs): .(x)
    """
    with pytest.raises(YATLSyntaxError):
        check(test, "", {"xs": []}, {})


def test_load_in_for():
    test = """
        .for (n in ns):
            .load_defaults_from: file.(n)
    """
    file1 = """
        file1: hello
    """
    file2 = """
        file2: howdy
    """
    expected = """
        - file1: hello
        - file2: howdy
    """
    check(test, expected, {"ns": [1, 2]}, {"file1": file1, "file2": file2})


def test_malformed_for():
    test = """
        .for(x): oops
    """
    with pytest.raises(YATLSyntaxError):
        check(test, "", {}, {})
