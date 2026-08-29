import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app import parse_schema
from expander import build_prompt, language_rule, parse_answer

ANSWER = """### Reasoning
The table "Emp_info" is about employees.
### Final Answer
emp_id: emp -> Employee, id -> Identifier
emp_nm: emp → Employee, nm → Name
doj: doj -> Date of Joining
"""


def test_parse_schema_splits_commas_and_newlines():
    assert parse_schema(" emp_id, emp_nm\ndept_cd ,\n\n") == ["emp_id", "emp_nm", "dept_cd"]


def test_parse_answer_handles_both_arrow_styles():
    results = parse_answer(ANSWER, ["emp_id", "emp_nm", "doj"])
    assert [r["expansion"] for r in results] == [
        "Employee Identifier",
        "Employee Name",
        "Date of Joining",
    ]
    assert results[0]["tokens"] == [
        {"token": "emp", "expansion": "Employee"},
        {"token": "id", "expansion": "Identifier"},
    ]


def test_parse_answer_keeps_request_order_and_reports_missing_columns():
    results = parse_answer(ANSWER, ["doj", "sal_amt"])
    assert [r["column"] for r in results] == ["doj", "sal_amt"]
    assert results[1]["tokens"] == []
    assert results[1]["expansion"] == ""


def test_build_prompt_includes_table_and_columns():
    user = build_prompt("Emp_info", ["emp_id", "sal_amt"], context="HR data")[1]["content"]
    assert "table named Emp_info" in user
    assert "emp_id | sal_amt" in user
    assert "HR data" in user


def test_build_prompt_defaults_to_language_detection():
    user = build_prompt("Cli_infos", ["nom_cli"])[1]["content"]
    assert "Detect the language of each column name" in user


def test_build_prompt_pins_requested_language():
    user = build_prompt("Cli_infos", ["nom_cli"], language="fr")[1]["content"]
    assert "The column names are in French" in user
    assert "Detect the language" not in user


def test_language_rule_falls_back_to_auto_for_unknown_code():
    assert language_rule("zz") == language_rule("auto")


def test_parse_answer_handles_accented_expansions():
    answer = """### Final Answer
dt_nais: dt -> Date, nais -> Naissance
état_cmd: état -> État, cmd -> Commande
"""
    results = parse_answer(answer, ["dt_nais", "état_cmd"])
    assert [r["expansion"] for r in results] == ["Date Naissance", "État Commande"]
