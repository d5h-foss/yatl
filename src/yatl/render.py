import re
from typing import Any, Dict, List, NamedTuple, Tuple

import yaml

from yatl.interpolation import render_interpolation
from yatl.types import JsonType, YATLEnvironmentError, YATLSyntaxError


class Def(NamedTuple):
    name: str
    args: List[str]
    body: JsonType


def render_from_obj(  # noqa: C901
    obj: JsonType, params: Dict[str, Any], defs: Dict[str, Def]
) -> JsonType:
    if isinstance(obj, dict):
        defaults_obj: JsonType = None
        rendered_obj: JsonType = {}
        last_if = None

        for key, value in obj.items():
            if isinstance(key, str) and key.startswith("."):
                # Note, elif and else require Python 3.7+ or a custom YAML loader to preserve key order.
                if _is_if(key):
                    rendered_obj, last_if = _render_if(
                        key, value, params, defs, rendered_obj
                    )
                elif _is_elif(key):
                    if last_if is None:
                        raise YATLSyntaxError(f"elif does not follow if: {key}")
                    if last_if is False:
                        rendered_obj, last_if = _render_if(
                            key, value, params, defs, rendered_obj
                        )
                elif key == ".else":
                    if last_if is None:
                        raise YATLSyntaxError(f"else does not follow if: {key}")
                    if last_if is False:
                        rendered_obj = _render_else(
                            key, value, params, defs, rendered_obj
                        )
                else:
                    last_if = None
                    if key == ".load_defaults_from":
                        defaults_obj = _load_defaults(obj, params)
                    elif _is_for(key):
                        # TODO: I can remove this restriction and use _shallow_merge.
                        if len(obj) != 1 or defaults_obj:
                            raise YATLSyntaxError(f"for loop must be by itself: {key}")
                        return _render_for(key, value, params, defs)
                    elif _is_def(key):
                        _store_def(key, value, defs)
                    elif _is_use(key):
                        rendered_obj = _render_use(
                            key, value, params, defs, rendered_obj
                        )
                    else:
                        _update_obj(rendered_obj, key, value, params, defs)
            else:
                last_if = None
                _update_obj(rendered_obj, key, value, params, defs)

        if defaults_obj:
            defaults_obj = render_from_obj(defaults_obj, params, defs)
            rendered_obj = _deep_merge_dicts(defaults_obj, rendered_obj)  # type: ignore

        return rendered_obj
    elif isinstance(obj, list):
        rendered_obj = []
        for elem in obj:
            rendered_elem = render_from_obj(elem, params, defs)
            if _can_extend_list(elem, rendered_elem):
                # Convert rendered_elem to [] if it's {}
                rendered_obj.extend(rendered_elem or [])  # type: ignore
            else:
                rendered_obj.append(rendered_elem)
        return rendered_obj
    elif isinstance(obj, str):
        return render_interpolation(obj, params)
    else:
        return obj


def _load_defaults(obj: dict, params: Dict[str, Any]) -> dict:
    value = obj[".load_defaults_from"]
    if not isinstance(value, str):
        raise YATLSyntaxError(f"load_defaults_from directive is not a string: {value}")

    filename = render_interpolation(value, params)
    if not isinstance(filename, str):
        raise YATLSyntaxError(
            f"load_defaults_from directive is not a string: {filename}"
        )

    defaults_obj = _load_yaml(filename)
    if not isinstance(defaults_obj, dict):
        raise YATLSyntaxError(f"{filename} must be an object at the top-level")
    return defaults_obj


def _is_if(key: str) -> bool:
    return bool(re.match(r"\.if\b", key))


def _is_elif(key: str) -> bool:
    return bool(re.match(r"\.elif\b", key))


def _render_if(
    if_key: str,
    if_value: JsonType,
    params: Dict[str, Any],
    defs: Dict[str, Def],
    rendered_obj: JsonType,
) -> Tuple[JsonType, bool]:
    # This regular expression captures both if and elif.
    if_match = re.match(r"\.(?:el)?if\s*\((.*)\)\s*$", if_key)
    if not if_match:
        raise YATLSyntaxError(f"Invalid if statement: {if_key}")

    condition = if_match[1].strip()
    if params[condition]:
        return _shallow_merge(if_key, if_value, params, defs, rendered_obj), True

    return rendered_obj, False


def _shallow_merge(
    key: str,
    value: JsonType,
    params: Dict[str, Any],
    defs: Dict[str, Def],
    rendered_obj: JsonType,
) -> JsonType:
    rendered_value = render_from_obj(value, params, defs)
    if not _can_merge_values(rendered_obj, rendered_value):
        raise YATLSyntaxError(
            f"Cannot merge {_type_name(rendered_value)} with {_type_name(rendered_obj)} in {key}"
        )

    if isinstance(rendered_value, dict):
        # Don't deep-merge, just shallow-update
        return {**rendered_obj, **rendered_value}  # type: ignore
    elif isinstance(rendered_value, list):
        rendered_obj = rendered_obj or []  # Convert {} to []
        return rendered_obj + rendered_value  # type: ignore
    else:
        return rendered_value


def _can_merge_values(parent_obj: JsonType, if_value: JsonType) -> bool:
    """Handle when there are multiple ifs in an object:

    Valid:

        foo: 1
        .if(y):
            bar: 2

    Invalid:

        .foo: 1
        .if(y):
            - 2
    """
    if not isinstance(parent_obj, dict) and not isinstance(parent_obj, list):
        # The parent object may be a scalar value if there are two ifs:
        #   .if(x): 1
        #   .if(y): 2
        return False
    if isinstance(parent_obj, dict) and not parent_obj:
        # The parent object is empty, so the if is the first node
        return True
    return type(parent_obj) == type(if_value)


def _type_name(x: Any) -> str:
    return type(x).__name__


def _render_else(
    key: str,
    value: JsonType,
    params: Dict[str, Any],
    defs: Dict[str, Def],
    rendered_obj: JsonType,
) -> JsonType:
    return _shallow_merge(key, value, params, defs, rendered_obj)


def _is_for(key: str) -> bool:
    return bool(re.match(r"\.for\b", key))


def _render_for(
    key: str, value: JsonType, params: Dict[str, Any], defs: Dict[str, Def]
) -> List:
    for_match = re.match(
        r"for\s*\(([a-zA-Z_][a-zA-Z0-9_]*)\s+in\s+([a-zA-Z_][a-zA-Z0-9_]*)\)\s*$",
        key[1:],
    )
    if not for_match:
        raise YATLSyntaxError(f"Invalid for statement: {key}")
    var = for_match[1].strip()
    param = for_match[2].strip()
    try:
        iterable = params[param]
    except KeyError:
        raise YATLEnvironmentError(f"Missing parameter {param}")
    rendered_list = []
    for elem in iterable:
        rendered_list.append(render_from_obj(value, {**params, var: elem}, defs))
    return rendered_list


def _can_extend_list(elem: JsonType, rendered_elem: JsonType) -> bool:
    if isinstance(elem, dict):
        # All keys must be directives.
        if any(not _is_directive(key) for key in elem):
            return False
        # The rendered object must be a list, or an empty object.
        if isinstance(rendered_elem, list):
            return True
        if isinstance(rendered_elem, dict) and not rendered_elem:
            return True
    return False


def _is_directive(key: str) -> bool:
    return (
        _is_if(key)
        or _is_elif(key)
        or key == ".else"
        or _is_for(key)
        or _is_def(key)
        or _is_use(key)
    )


def _is_def(key: str) -> bool:
    return bool(re.match(r"\.def\b", key))


def _store_def(key: str, value: JsonType, defs: Dict[str, Def]) -> None:
    name, args = _parse_def_parts(key)
    if len(args) != len({*args}):
        raise YATLSyntaxError(f"Duplicate name in def arguments: {key}")
    defs[name] = Def(name, args, value)


def _parse_def_parts(key: str) -> Tuple[str, List[str]]:
    name_match = re.match(
        r"""
            \.def \s+
            ([a-zA-Z_][a-zA-Z0-9_]*) \s*  # Capture the name
        """,
        key,
        re.VERBOSE,
    )
    if not name_match:
        raise YATLSyntaxError(f"Malformed def directive: {key}")

    name = name_match[1]
    if name_match.end() == len(key):
        # Handle ".def foo:"
        return name, []

    args = key[name_match.end() :]
    args_match = re.match(
        r"""
            \( \s* (  # Capture the arg list
                (?:[a-zA-Z_][a-zA-Z0-9_]*)  # First arg
                (?: \s* , \s*
                    [a-zA-Z_][a-zA-Z0-9_]*  # Subsequent args
                )*
            )? \s* \) \s* $
        """,
        args,
        re.VERBOSE,
    )
    if not args_match:
        raise YATLSyntaxError(f"Malformed def arguments: {key}")
    if not args_match[1]:
        # Handle ".def foo():"
        return name, []

    return name, [a.strip() for a in args_match[1].split(",")]


def _is_use(key: str) -> bool:
    return bool(re.match(r"\.use\b", key))


def _render_use(
    key: str,
    value: JsonType,
    params: Dict[str, Any],
    defs: Dict[str, Def],
    rendered_obj: JsonType,
) -> JsonType:
    name = _parse_use_name(key)
    if name not in defs:
        raise YATLEnvironmentError(f"Invalid name for use: {name}")
    df = defs[name]
    args = _parse_use_args(value, df)
    return _shallow_merge(key, df.body, {**params, **args}, defs, rendered_obj)


def _parse_use_name(key: str) -> str:
    name_match = re.match(
        r"""
            \.use \s+
            ([a-zA-Z_][a-zA-Z0-9_]*) \s*  # Capture the name
        """,
        key,
        re.VERBOSE,
    )
    if not name_match:
        raise YATLSyntaxError(f"Malformed use directive: {key}")
    return name_match[1]


def _parse_use_args(value: JsonType, df: Def) -> Dict[str, JsonType]:
    if not df.args:
        if value:
            raise YATLSyntaxError(
                f"def {df.name} takes no args but use directive passed a non-empty object"
            )
        return {}

    if isinstance(value, dict):
        return _create_use_args_from_dict(value, df)
    elif isinstance(value, list):
        return _create_use_args_from_list(value, df)
    else:
        if len(df.args) != 1:
            raise YATLSyntaxError(
                f"def {df.name} takes {len(df.args)} args but is given a value; pass an object or list instead"
            )
        return {df.args[0]: value}


def _create_use_args_from_dict(value: dict, df: Def) -> Dict[str, JsonType]:
    expected_args = {*df.args}
    received_args = {*value.keys()}
    if expected_args != received_args:
        expected = ", ".join(df.args)
        received = ", ".join(value.keys())
        raise YATLSyntaxError(
            f"def {df.name} expected args ({expected}) but received ({received})"
        )

    return value


def _create_use_args_from_list(value: list, df: Def) -> Dict[str, JsonType]:
    if len(df.args) != len(value):
        expected = ", ".join(df.args)
        received = len(value)
        raise YATLSyntaxError(
            f"def {df.name} expected args ({expected}) but received {received} args instead"
        )

    return dict(zip(df.args, value))


def _update_obj(
    obj: JsonType,
    key: str,
    value: JsonType,
    params: Dict[str, Any],
    defs: Dict[str, Def],
) -> None:
    if not isinstance(obj, dict):
        raise YATLSyntaxError(f"Cannot add field {key} to non-object")
    interpolated_key = render_interpolation(key, params)
    obj[interpolated_key] = render_from_obj(value, params, defs)


def _load_yaml(path: str) -> str:
    with open(path) as f:
        return yaml.safe_load(f)


def _deep_merge_dicts(defaults: dict, updates: dict) -> dict:
    """Merges two dicts recursively, with updates taking precendence.

    Note that this modifies defaults in place.
    """
    for k, u in updates.items():
        if k not in defaults:
            defaults[k] = u
        else:
            v = defaults[k]
            if isinstance(u, dict) and isinstance(v, dict):
                defaults[k] = _deep_merge_dicts(v, u)
            else:
                defaults[k] = u

    return defaults
