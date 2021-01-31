import pytest

from tests.helpers import check
from yatl.interpolation import render_interpolation
from yatl.types import YATLEnvironmentError, YATLSyntaxError


def test_render_interpolation():
    assert (
        render_interpolation(".(foo) and .(bar)", {"foo": "abc", "bar": "xyz"})
        == "abc and xyz"
    )


def test_render_interpolation_escape():
    assert render_interpolation(r"\.(foo)", {"foo": "abc"}) == r"\.(foo)"


def test_render_interpolation_incomplete():
    with pytest.raises(YATLSyntaxError):
        render_interpolation(".(", {})


def test_render_interpolation_dot():
    assert render_interpolation(".", {}) == "."


def test_interpolation_in_value():
    test = """
        .(foo)
    """
    expected = """
        bar
    """
    check(test, expected, {"foo": "bar"}, {})


def test_interpolation_in_object():
    test = """
        foo: .(bar)
    """
    expected = """
        foo: baz
    """
    check(test, expected, {"bar": "baz"}, {})


def test_bad_interpolation_param():
    test = """
        foo: .(oops)
    """
    with pytest.raises(YATLEnvironmentError):
        check(test, "", {}, {})


def test_interpolation_in_array():
    test = """
        - .(foo)
    """
    expected = """
        - bar
    """
    check(test, expected, {"foo": "bar"}, {})


def test_two_interpolations():
    test = """
        .(foo) and .(bar)
    """
    expected = """
        abc and xyz
    """
    check(test, expected, {"foo": "abc", "bar": "xyz"}, {})


def test_int_interpolation():
    test = """
        - .(foo)
    """
    expected = """
        - 1
    """
    check(test, expected, {"foo": 1}, {})
