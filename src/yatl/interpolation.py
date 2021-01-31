from typing import Any, Dict, Iterable, Tuple

from yatl.types import YATLEnvironmentError, YATLSyntaxError


def render_interpolation(s: str, params: Dict[str, Any]) -> str:
    input_parts = parse_expressions(s)
    evaled_parts = [
        (evaluate(p, params) if is_expr else p) for p, is_expr in input_parts
    ]
    if len(evaled_parts) == 1:
        # Preserve whatever type it is
        return evaled_parts[0]
    else:
        return "".join(str(part) for part in evaled_parts)


def parse_expressions(s: str) -> Iterable[Tuple[str, bool]]:
    parts = []
    i = 0
    while i < len(s):
        if s[i : i + 2] == ".(":
            if s[:i]:
                parts.append((s[:i], False))
            expr, s = parse_expression(s[i + 2 :])
            parts.append((expr, True))
        elif s[i : i + 2] == r"\.":
            i += 2
        else:
            i += 1

    if s:
        parts.append((s, False))
    return parts


def parse_expression(s: str) -> Tuple[str, str]:
    paren_nesting = 0
    i = 0
    while i < len(s):
        if s[i] == "(":
            paren_nesting += 1
        elif s[i] == ")":
            paren_nesting -= 1

        # TODO: Handle embedded strings
        if paren_nesting < 0:
            return s[:i], s[i + 1 :]

        i += 1

    raise YATLSyntaxError("Could not find end of expression")


def evaluate(s: str, params: Dict[str, Any]) -> Any:
    # TODO: Actual evaluation
    try:
        return params[s]
    except KeyError:
        raise YATLEnvironmentError(f"Missing parameter {s}")
