import os
import runpy

import test1_code

MODULE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test1_code.py")


def test_prints_each_value_on_its_own_line(capsys):
    test1_code.test()

    assert capsys.readouterr().out == "1\n4\n9\n8\n"


def test_returns_none(capsys):
    assert test1_code.test() is None
    capsys.readouterr()


def test_module_run_as_script_prints_values(capsys):
    runpy.run_path(MODULE_PATH, run_name="__main__")

    assert capsys.readouterr().out == "1\n4\n9\n8\n"


def test_import_does_not_print(capsys):
    runpy.run_path(MODULE_PATH, run_name="not_main")

    assert capsys.readouterr().out == ""
