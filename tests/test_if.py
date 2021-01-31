import pytest

from tests.helpers import check
from yatl.types import YATLSyntaxError


def test_if_true_in_object():
    test = """
        outer:
            .if (foo):
                inner: 1
    """
    expected = """
        outer:
            inner: 1
    """
    check(test, expected, {"foo": True}, {})


def test_if_false_in_object():
    test = """
        outer:
            .if (foo):
                inner: 1
    """
    expected = """
        outer:
            {}
    """
    check(test, expected, {"foo": False}, {})


def test_load_same_if_as_parent():
    test = """
        outer:
            .if (foo):
                a: winner
                .load_defaults_from: file1
    """
    file1 = """
        .if (foo):
            a: loser
            b: winner
    """
    file1_different_whitespace = """
        .if(foo):
            a: loser
            b: winner
    """
    expected = """
        outer:
            a: winner
            b: winner
    """
    check(test, expected, {"foo": True}, {"file1": file1})
    check(test, expected, {"foo": True}, {"file1": file1_different_whitespace})


def test_load_nonexistent_file_in_if_false():
    """It should not crash by trying to load a nonexistent file in an if(false) block."""

    test = """
        outer:
            .if (foo):
                .load_defaults_from: nonexistent
    """
    expected = """
        outer:
            {}
    """
    check(test, expected, {"foo": False}, {})


def test_if_true_in_list():
    test = """
        foo:
            - bar
            - .if (x):
                - baz
    """
    expected = """
        foo:
            - bar
            - baz
    """
    check(test, expected, {"x": True}, {})


def test_if_false_in_list():
    test = """
        foo:
            - bar
            - .if (x):
                - baz
    """
    expected = """
        foo:
            - bar
    """
    check(test, expected, {"x": False}, {})


def test_if_returns_list():
    test = """
        .if (x):
            - foo
    """
    expected = """
        - foo
    """
    check(test, expected, {"x": True}, {})


def test_double_if_returns_list():
    test = """
        .if(x):
            - foo
        .if (x):
            - bar
    """
    expected = """
        - foo
        - bar
    """
    check(test, expected, {"x": True}, {})


def test_malformed_if():
    test = """
        .if: oops
    """
    with pytest.raises(YATLSyntaxError):
        check(test, "", {}, {})


def test_unmergeable_if_scalars():
    test = """
        .if(x): 1
        .if (x): 2
    """
    with pytest.raises(YATLSyntaxError):
        check(test, "", {"x": True}, {})


def test_unmergeable_if_dict_and_list():
    test = """
        .if(x):
            foo: a
        .if (x):
            - b
    """
    with pytest.raises(YATLSyntaxError):
        check(test, "", {"x": True}, {})


def test_unmergeable_if_list_and_dict():
    test = """
        .if(x):
            - b
        .if (x):
            foo: a
    """
    with pytest.raises(YATLSyntaxError):
        check(test, "", {"x": True}, {})


def test_unmergeable_fields_after_if():
    test = """
        .if (x): 1
        foo: 2
    """
    with pytest.raises(YATLSyntaxError):
        check(test, "", {"x": True}, {})


def test_if_does_not_extend_list():
    test = """
        - foo
        - .if (x):
            bar: baz
    """
    expected = """
        - foo
        - bar: baz
    """
    check(test, expected, {"x": True}, {})


def test_elif_true_true():
    test = """
        .if(x):
            foo: 1
        .elif (x):
            bar: 2
    """
    expected = """
        foo: 1
    """
    check(test, expected, {"x": True}, {})


def test_elif_true_false():
    test = """
        .if (x):
            foo: 1
        .elif (y):
            bar: 2
    """
    expected = """
        foo: 1
    """
    check(test, expected, {"x": True, "y": False}, {})


def test_elif_false_true():
    test = """
        .if (x):
            foo: 1
        .elif (y):
            bar: 2
    """
    expected = """
        bar: 2
    """
    check(test, expected, {"x": False, "y": True}, {})


def test_elif_false_false():
    test = """
        .if (x):
            foo: 1
        .elif (y):
            bar: 2
    """
    expected = """
        {}
    """
    check(test, expected, {"x": False, "y": False}, {})


def test_three_elif():
    test = """
        .if (x):
            foo: 1
        .elif (y):
            bar: 2
        .elif (z):
            baz: 3
    """
    expected = """
        baz: 3
    """
    check(test, expected, {"x": False, "y": False, "z": True}, {})


def test_elif_alone():
    test = """
        .elif (x): a
    """
    with pytest.raises(YATLSyntaxError):
        check(test, "", {"x": True}, {})


def test_elif_before_if():
    test = """
        .elif (x): a
        .if (x): b
    """
    with pytest.raises(YATLSyntaxError):
        check(test, "", {"x": True}, {})


def test_break_before_elif():
    test = """
        .if (x):
            foo: 1
        bar: 2
        .elif (x):
            baz: 3
    """
    with pytest.raises(YATLSyntaxError):
        check(test, "", {"x": True}, {})


def test_elif_in_list():
    test = """
        - .if (x):
            - foo
            - food
          .elif (x):
            - bar
            - bard
    """
    expected = """
        - foo
        - food
    """
    check(test, expected, {"x": True}, {})


def test_if_true_else():
    test = """
        .if (x):
            foo: 1
        .else:
            bar: 2
    """
    expected = """
        foo: 1
    """
    check(test, expected, {"x": True}, {})


def test_if_false_else():
    test = """
        .if (x):
            foo: 1
        .else:
            bar: 2
    """
    expected = """
        bar: 2
    """
    check(test, expected, {"x": False}, {})


def test_if_elif_else():
    test = """
        .if (x):
            foo: 1
        .elif (x):
            bar: 2
        .else:
            baz: 3
    """
    expected = """
        baz: 3
    """
    check(test, expected, {"x": False}, {})


def test_else_alone():
    test = """
        .else: a
    """
    with pytest.raises(YATLSyntaxError):
        check(test, "", {"x": True}, {})


def test_break_before_else():
    test = """
        .if (x):
            foo: 1
        bar: 2
        .else:
            baz: 3
    """
    with pytest.raises(YATLSyntaxError):
        check(test, "", {"x": True}, {})


def test_list_in_list():
    test = """
        - .if (x):
            -
                - foo
                - food
    """
    expected = """
        - ["foo", "food"]
    """
    check(test, expected, {"x": True}, {})
