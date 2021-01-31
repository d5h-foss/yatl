from contextlib import contextmanager
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent
from typing import Any, Dict

import yaml

from yatl import load


def check(
    test_yaml: str, expected_yaml: str, params: Dict[str, Any], files: Dict[str, str]
) -> None:
    with _temp_dir():
        for filename, contents in files.items():
            _write_yaml(filename, contents)
        test_obj = load(test_yaml, params)

    expected_obj = yaml.safe_load(dedent(expected_yaml))
    assert expected_obj == test_obj


@contextmanager
def _temp_dir():
    with TemporaryDirectory() as path:
        cwd = os.getcwd()
        try:
            os.chdir(path)
            yield
        finally:
            os.chdir(cwd)


def _write_yaml(filename: str, contents: str) -> None:
    Path(filename).write_text(dedent(contents))
