import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app import parse_schema
from expander import build_prompt, parse_answer

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
