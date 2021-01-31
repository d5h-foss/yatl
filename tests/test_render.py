from tests.helpers import check


def test_unrecognized_directive_is_left_alone():
    test = """
        .hello:
            {}
    """
    expected = """
        .hello:
            {}
    """
    check(test, expected, {}, {})
