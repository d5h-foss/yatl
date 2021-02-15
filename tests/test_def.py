import pytest

from tests.helpers import check
from yatl.types import YATLEnvironmentError, YATLSyntaxError


def test_one_arg_def_passed_as_value():
    test = """
        .def foo(x):
            .(x)-key: .(x)-value
        .use foo: bar
    """
    expected = """
        bar-key: bar-value
    """
    check(test, expected, {}, {})


def test_one_arg_def_passed_by_name():
    test = """
        .def foo(x):
            .(x)-key: .(x)-value
        .use foo:
            x: bar
    """
    expected = """
        bar-key: bar-value
    """
    check(test, expected, {}, {})


def test_one_arg_def_passed_by_list():
    test = """
        .def foo(x):
            .(x)-key: .(x)-value
        .use foo:
            - bar
    """
    expected = """
        bar-key: bar-value
    """
    check(test, expected, {}, {})


def test_two_arg_def_passed_as_value():
    test = """
        .def foo(k, v):
            .(k): .(v)
        .use foo: oops error
    """
    with pytest.raises(YATLSyntaxError):
        check(test, "", {}, {})


def test_two_arg_def_passed_by_name():
    test = """
        .def foo(k, v):
            .(k): .(v)
        .use foo:
            k: key
            v: value
    """
    expected = """
        key: value
    """
    check(test, expected, {}, {})


def test_two_arg_def_passed_by_list():
    test = """
        .def foo(k, v):
            .(k): .(v)
        .use foo:
            - key
            - value
    """
    expected = """
        key: value
    """
    check(test, expected, {}, {})


def test_different_arg_types():
    test = """
        .def foo(str, int, list, dict):
            str: .(str)
            int: .(int)
            list: .(list)
            dict: .(dict)
        .use foo:
            str: foo
            int: 42
            list: [1, 1, 2, 3]
            dict:
                foo: bar
    """
    expected = """
        str: foo
        int: 42
        list: [1, 1, 2, 3]
        dict:
            foo: bar
    """
    check(test, expected, {}, {})


def test_zero_arg_def_with_parens():
    test = """
        .def foo():
            key: val
        .use foo: {}
    """
    expected = """
        key: val
    """
    check(test, expected, {}, {})


def test_zero_arg_def_with_no_parens():
    test = """
        .def foo:
            key: val
        .use foo: {}
    """
    expected = """
        key: val
    """
    check(test, expected, {}, {})


def test_zero_arg_def_with_empty_string():
    test = """
        .def foo:
            key: val
        .use foo: ""
    """
    expected = """
        key: val
    """
    check(test, expected, {}, {})


def test_zero_arg_def_with_empty_list():
    test = """
        .def foo:
            key: val
        .use foo: []
    """
    expected = """
        key: val
    """
    check(test, expected, {}, {})


def test_def_returning_list_used_in_list_extends_it():
    test = """
        .def foo: [1, 1, 2, 3]
        list:
            - .use foo: ""
            - 5
    """
    expected = """
        list:
            - 1
            - 1
            - 2
            - 3
            - 5
    """
    check(test, expected, {}, {})


def test_use_defs_when_top_level_is_list():
    test = """
        .def foo(x): .(x)
        .def top:
            - .use foo: a
            - .use foo: b
        .use top: []
    """
    expected = """
        - a
        - b
    """
    check(test, expected, {}, {})


def test_def_args_shadow_params():
    test = """
        .def foo(x):
            during: .(x)
        before: .(x)
        .use foo: ham
        after: .(x)
    """
    expected = """
        before: eggs
        during: ham
        after: eggs
    """
    check(test, expected, {"x": "eggs"}, {})


def redefine_def():
    test = """
        .def foo: first
        .def foo: second
        .use foo: []
    """
    expected = """
        second
    """
    check(test, expected, {}, {})


def load_def():
    test = """
        .load_defaults_from: file1
        .use foo: ""
    """
    file1 = """
        .def foo: bar
    """
    expected = """
        bar
    """
    check(test, expected, {}, {"file1": file1})


def defs_are_global():
    test = """
        defs:
            .def foo:
                bar: baz
        .use foo: ""
    """
    expected = """
        defs: {}
        bar: baz
    """
    check(test, expected, {}, {})


def def_in_def():
    test = """
        .def outer(x):
            .def inner(y): .(x)-.(y)
        .use outer: a
        before:
            .use inner: b
        .use outer: c
        after:
            .use inner: d
    """
    expected = """
        before: a-b
        after: c-d
    """
    check(test, expected, {}, {})


def test_zero_arg_def_with_something_truthy():
    test = """
        .def foo:
            key: val
        .use foo: blah
    """
    with pytest.raises(YATLSyntaxError):
        check(test, "", {}, {})


def test_def_with_no_name():
    test = """
        .def: {}
    """
    with pytest.raises(YATLSyntaxError):
        check(test, "", {}, {})


def test_def_with_same_arg_names():
    test = """
        .def foo(x, x): {}
    """
    with pytest.raises(YATLSyntaxError):
        check(test, "", {}, {})


def test_def_with_unclosed_parens():
    test = """
        .def foo(x: {}
    """
    with pytest.raises(YATLSyntaxError):
        check(test, "", {}, {})


def test_def_with_missing_args_in_list():
    test = """
        .def foo(x): {}
        .use foo: []
    """
    with pytest.raises(YATLSyntaxError):
        check(test, "", {}, {})


def test_def_with_extra_args_in_list():
    test = """
        .def foo(x): {}
        .use foo: [1, 2]
    """
    with pytest.raises(YATLSyntaxError):
        check(test, "", {}, {})


def test_def_with_missing_args_in_obj():
    test = """
        .def foo(x): {}
        .use foo: {}
    """
    with pytest.raises(YATLSyntaxError):
        check(test, "", {}, {})


def test_def_with_extra_args_in_obj():
    test = """
        .def foo(x): {}
        .use foo:
            x: foo
            y: bar
    """
    with pytest.raises(YATLSyntaxError):
        check(test, "", {}, {})


def test_def_with_wrong_arg():
    test = """
        .def foo(x): {}
        .use foo:
            y: bar
    """
    with pytest.raises(YATLSyntaxError):
        check(test, "", {}, {})


def test_def_that_returns_list_in_obj():
    test = """
        .def foo: []
        a: b
        .use foo: ""
    """
    with pytest.raises(YATLSyntaxError):
        check(test, "", {}, {})


def test_def_that_returns_value_in_obj():
    test = """
        .def foo: bar
        a: b
        .use foo: ""
    """
    with pytest.raises(YATLSyntaxError):
        check(test, "", {}, {})


def test_def_does_not_exist():
    test = """
        .use foo: ""
    """
    with pytest.raises(YATLEnvironmentError):
        check(test, "", {}, {})


def test_malformed_use():
    test = """
        .def foo: bar
        .use (foo): ""
    """
    with pytest.raises(YATLSyntaxError):
        check(test, "", {}, {})
