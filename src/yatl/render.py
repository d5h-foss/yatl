import re
from typing import Any, Dict, List, Tuple

import yaml

from yatl.interpolation import render_interpolation
from yatl.types import JsonType, YATLEnvironmentError, YATLSyntaxError


def render_from_obj(obj: JsonType, params: Dict[str, Any]) -> JsonType:
    if isinstance(obj, dict):
        defaults_obj: JsonType = None
        rendered_obj: JsonType = {}
        last_if = None

        for key, value in obj.items():
            if isinstance(key, str) and key.startswith("."):
                # Note, elif and else require Python 3.7+ or a custom YAML loader to preserve key order.
                if _is_if(key):
                    rendered_obj, last_if = _render_if(key, value, params, rendered_obj)
                elif _is_elif(key):
                    if last_if is None:
                        raise YATLSyntaxError(f"elif does not follow if: {key}")
                    if last_if is False:
                        rendered_obj, last_if = _render_if(
                            key, value, params, rendered_obj
                        )
                elif key == ".else":
                    if last_if is None:
                        raise YATLSyntaxError(f"else does not follow if: {key}")
                    if last_if is False:
                        rendered_obj = _render_else(key, value, params, rendered_obj)
                else:
                    last_if = None
                    if key == ".load_defaults_from":
                        defaults_obj = _load_defaults(obj, params)
                    elif _is_for(key):
                        # TODO: I can remove this restriction and use _shallow_merge.
                        if len(obj) != 1 or defaults_obj:
                            raise YATLSyntaxError(f"for loop must be by itself: {key}")
                        return _render_for(key, value, params)
                    else:
                        _update_obj(rendered_obj, key, value, params)
            else:
                last_if = None
                _update_obj(rendered_obj, key, value, params)

        if defaults_obj:
            defaults_obj = render_from_obj(defaults_obj, params)
            rendered_obj = _deep_merge_dicts(defaults_obj, rendered_obj)  # type: ignore

        return rendered_obj
    elif isinstance(obj, list):
        rendered_obj = []
        for elem in obj:
            rendered_elem = render_from_obj(elem, params)
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
    filename = render_interpolation(obj[".load_defaults_from"], params)
    defaults_obj = _load_yaml(filename)
    if not isinstance(defaults_obj, dict):
        raise YATLSyntaxError(f"{filename} must be an object at the top-level")
    return defaults_obj


def _is_if(key: str) -> bool:
    return bool(re.match(r"\.if\b", key))


def _is_elif(key: str) -> bool:
    return bool(re.match(r"\.elif\b", key))


def _render_if(
    if_key: str, if_value: JsonType, params: Dict[str, Any], rendered_obj: JsonType
) -> Tuple[JsonType, bool]:
    # This regular expression captures both if and elif.
    if_match = re.match(r"\.(?:el)?if\s*\((.*)\)\s*$", if_key)
    if not if_match:
        raise YATLSyntaxError(f"Invalid if statement: {if_key}")

    condition = if_match.group(1).strip()
    if params[condition]:
        return _shallow_merge(if_key, if_value, params, rendered_obj), True

    return rendered_obj, False


def _shallow_merge(
    key: str, value: JsonType, params: Dict[str, Any], rendered_obj: JsonType
) -> JsonType:
    rendered_value = render_from_obj(value, params)
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
    key: str, value: JsonType, params: Dict[str, Any], rendered_obj: JsonType
) -> JsonType:
    return _shallow_merge(key, value, params, rendered_obj)


def _is_for(key: str) -> bool:
    return bool(re.match(r"\.for\b", key))


def _render_for(key: str, value: JsonType, params: Dict[str, Any]) -> List:
    for_match = re.match(
        r"for\s*\(([a-zA-Z_][a-zA-Z0-9_]*)\s+in\s+([a-zA-Z_][a-zA-Z0-9_]*)\)\s*$",
        key[1:],
    )
    if not for_match:
        raise YATLSyntaxError(f"Invalid for statement: {key}")
    var = for_match.group(1).strip()
    param = for_match.group(2).strip()
    try:
        iterable = params[param]
    except KeyError:
        raise YATLEnvironmentError(f"Missing parameter {param}")
    rendered_list = []
    for elem in iterable:
        rendered_list.append(render_from_obj(value, {**params, var: elem}))
    return rendered_list


def _can_extend_list(elem: JsonType, rendered_elem: JsonType) -> bool:
    if isinstance(elem, dict):
        # The first key must be an if or for.
        key = next(iter(elem))
        if not _is_if(key) and not _is_for(key):
            return False
        # The rendered object must be a list, or an empty object.
        if isinstance(rendered_elem, list):
            return True
        if isinstance(rendered_elem, dict) and not rendered_elem:
            return True
    return False


def _update_obj(
    obj: JsonType, key: str, value: JsonType, params: Dict[str, Any]
) -> None:
    if not isinstance(obj, dict):
        raise YATLSyntaxError(f"Cannot add field {key} to non-object")
    obj[key] = render_from_obj(value, params)


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
