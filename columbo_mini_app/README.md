# Columbo mini — column name expander

Takes a table schema (column names) plus an LLM API key and returns, for each column, its
full-form expansion together with the per-token mapping (`sal_amt` → `sal -> Salary, amt -> Amount`).

The prompt and the `token -> expansion` output contract follow the column-expansion stage of
[Columbo](https://github.com/anhaidgroup/columbo); this app is the single-table, single-call
version of it (no table clustering, no cross-table token revision, no evaluation).

## Run

```bash
pip install -r requirements.txt
uvicorn app:app --reload --port 8000   # from inside columbo_mini_app/
```

Open http://localhost:8000 — paste columns, optionally the table name and a one-line dataset
context, paste an OpenAI key, and submit. If the server has `OPENAI_API_KEY` set, the key field
can be left empty.

## API

```bash
curl -s localhost:8000/api/expand -H 'content-type: application/json' -d '{
  "schema_text": "emp_id, emp_nm, dept_cd, doj, sal_amt",
  "table_name": "Emp_info",
  "api_key": "sk-..."
}'
```

```json
{
  "table_name": "Emp_info",
  "results": [
    {"column": "emp_id", "tokens": [{"token": "emp", "expansion": "Employee"},
                                    {"token": "id", "expansion": "Identifier"}],
     "expansion": "Employee Identifier"}
  ],
  "raw": "### Reasoning ..."
}
```

The API key is used only for the request it arrives on: it is never written to disk or logged.

## Tests

```bash
python -m pytest columbo_mini_app
```

`test_expander.py` covers schema parsing and the answer parser (arrow variants, unknown columns)
without calling the LLM.
