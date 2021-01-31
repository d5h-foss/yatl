from typing import Union

# JsonType = Union[Dict[str, "JsonType"], List["JsonType"], str, int, float, bool, None]
# MyPy doesn't support recursive types yet. Just use an alias mainly for documentation, not strong type checking.
JsonType = Union[dict, list, str, int, float, bool, None]


class YATLError(Exception):
    pass


class YATLEnvironmentError(YATLError):
    pass


class YATLSyntaxError(YATLError):
    pass
