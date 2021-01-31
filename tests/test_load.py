import pytest

from tests.helpers import check
from yatl.types import YATLSyntaxError


def test_load():
    test = """
        top:
            .load_defaults_from: file1
            one: 1
    """
    file1 = """
        two: 2
    """
    expected = """
        top:
            one: 1
            two: 2
    """
    check(test, expected, {}, {"file1": file1})


def test_load_in_list():
    test = """
        top:
            - .load_defaults_from: file1
            - two: 2
    """
    file1 = """
        one: 1
    """
    expected = """
        top:
            - one: 1
            - two: 2
    """
    check(test, expected, {}, {"file1": file1})


def test_update_defaults():
    test = """
        top:
            .load_defaults_from: file1
            one: 1
    """
    file1 = """
        one: will update
    """
    expected = """
        top:
            one: 1
    """
    check(test, expected, {}, {"file1": file1})


def test_nested_update():
    test = """
        outer:
            .load_defaults_from: file1
            outer-one: 1
            inner:
                inner-one: 1
                inner-two: 2
    """
    file1 = """
        outer-two: 2
        inner:
            inner-two: will update
            inner-three: 3
    """
    expected = """
        outer:
            outer-one: 1
            outer-two: 2
            inner:
                inner-one: 1
                inner-two: 2
                inner-three: 3
    """
    check(test, expected, {}, {"file1": file1})


def test_nested_nondict_over_dict():
    test = """
        outer:
            .load_defaults_from: file1
            inner: winner
    """
    file1 = """
        inner:
            inner-inner: chicken dinner
    """
    expected = """
        outer:
            inner: winner
    """
    check(test, expected, {}, {"file1": file1})


def test_nested_load():
    test = """
        top:
            .load_defaults_from: file1
            test-0: test winner
            test-3: test winner
    """
    file1 = """
        .load_defaults_from: file2
        test-0: file1 loser
        test-1: file1 winner
    """
    file2 = """
        test-0: file2 loser
        test-1: file2 loser
        test-2: file2 winner
        test-3: file2 loser
    """
    expected = """
        top:
            test-0: test winner
            test-1: file1 winner
            test-2: file2 winner
            test-3: test winner
    """
    check(test, expected, {}, {"file1": file1, "file2": file2})


def test_merge_conflict():
    # When there are conflicts at the same recursion level, the most nested object should win.
    test = """
        outer:
            .load_defaults_from: file1
            inner:
                .load_defaults_from: file2
    """
    file1 = """
        inner:
            test: loser
    """
    file2 = """
        test: winner
    """
    expected = """
        outer:
            inner:
                test: winner
    """
    check(test, expected, {}, {"file1": file1, "file2": file2})


def test_load_updating_load():
    test = """
        outer:
            .load_defaults_from: file1
            inner:
                test-0: test winner
                .load_defaults_from: file2
    """
    file1 = """
        inner:
            test-1: file1 loser
            .load_defaults_from: file3
    """
    file2 = """
        test-1: file2 winner
        test-2: file2 winner
    """
    file3 = """
        test-1: file3 loser
        test-2: file3 loser
        test-3: file3 only
    """
    expected = """
        outer:
            inner:
                test-0: test winner
                test-1: file2 winner
                test-2: file2 winner
                test-3: file3 only
    """
    check(test, expected, {}, {"file1": file1, "file2": file2, "file3": file3})


def test_non_object_file():
    test = """
        top:
            .load_defaults_from: non_object
    """
    non_object = """
        "string"
    """
    with pytest.raises(YATLSyntaxError):
        check(test, "", {}, {"non_object": non_object})
