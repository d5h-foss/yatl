import pytest

from tests.helpers import check
from yatl.types import YATLSyntaxError


def test_load():
    test = """
        .load: file1
    """
    file1 = """
        one: 1
    """
    expected = """
        one: 1
    """
    check(test, expected, {}, {"file1": file1})


def test_load_list():
    test = """
        .load:
            - file1
            - file2
    """
    file1 = """
        one: 1
    """
    file2 = """
        two: 2
    """
    expected = """
        one: 1
        two: 2
    """
    check(test, expected, {}, {"file1": file1, "file2": file2})


def test_load_list_overwrite():
    test = """
        .load:
            - file1
            - file2
    """
    file1 = """
        one: 0
    """
    file2 = """
        one: 1
    """
    expected = """
        one: 1
    """
    check(test, expected, {}, {"file1": file1, "file2": file2})


def test_load_in_list():
    test = """
        - .load: file1
    """
    file1 = """
        foo
    """
    expected = """
        - foo
    """
    check(test, expected, {}, {"file1": file1})


def test_load_list_extends_list():
    test = """
        - .load: file1
    """
    file1 = """
        - foo
    """
    expected = """
        - foo
    """
    check(test, expected, {}, {"file1": file1})


def test_load_interpolated_name():
    test = """
        .load: .(filename)
    """
    file1 = """
        foo
    """
    expected = """
        foo
    """
    check(test, expected, {"filename": "file1"}, {"file1": file1})


def test_load_non_string():
    test = """
        top:
            .load: {}
    """
    file1 = """
        {}
    """
    with pytest.raises(YATLSyntaxError):
        check(test, "", {}, {"{}": file1})


def test_load_interpolated_non_string():
    test = """
        top:
            .load: .(filename)
    """
    file1 = """
        {}
    """
    with pytest.raises(YATLSyntaxError):
        check(test, "", {"filename": {}}, {"{}": file1})


def test_load_defaults_from():
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


def test_load_defaults_from_in_list():
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


def test_nested_load_defaults_from():
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


def test_defaults_updating_defaults():
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


def test_load_list_of_defaults():
    test = """
        .load_defaults_from:
            - file1
            - file2
        main: yes
    """
    file1 = """
        file1: yes
        file2: no
    """
    file2 = """
        file2: yes
        main: no
    """
    expected = """
        file1: yes
        file2: yes
        main: yes
    """
    check(test, expected, {}, {"file1": file1, "file2": file2})


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


def test_load_arg_is_int():
    test = """
        top:
            .load_defaults_from: 1
    """
    file1 = """
        {}
    """
    with pytest.raises(YATLSyntaxError):
        check(test, "", {}, {"1": file1})


def test_load_arg_is_obj():
    test = """
        top:
            .load_defaults_from: {}
    """
    file1 = """
        {}
    """
    with pytest.raises(YATLSyntaxError):
        check(test, "", {}, {"{}": file1})


def test_load_interpolated_arg_is_obj():
    test = """
        top:
            .load_defaults_from: .(filename)
    """
    file1 = """
        {}
    """
    with pytest.raises(YATLSyntaxError):
        check(test, "", {"filename": {}}, {"{}": file1})
