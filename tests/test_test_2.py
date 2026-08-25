import os
import runpy

import pytest

import test_2

MODULE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_2.py")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (444, "444\n"),
        (0, "0\n"),
        (-7, "-7\n"),
        ("hello", "hello\n"),
        (None, "None\n"),
        ([1, 2], "[1, 2]\n"),
    ],
)
def test_prints_value(capsys, value, expected):
    test_2.simple(value)

    assert capsys.readouterr().out == expected


def test_returns_none(capsys):
    assert test_2.simple(1) is None
    capsys.readouterr()


def test_requires_an_argument():
    with pytest.raises(TypeError):
        test_2.simple()


def test_module_run_as_script_prints_default_value(capsys):
    runpy.run_path(MODULE_PATH, run_name="__main__")

    assert capsys.readouterr().out == "444\n"


def test_import_does_not_print(capsys):
    runpy.run_path(MODULE_PATH, run_name="not_main")

    assert capsys.readouterr().out == ""
