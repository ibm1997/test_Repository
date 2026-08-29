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

## Languages

Column names do not have to be English. The expansions are always written in the language of the
column names, so `nom_cli, dt_nais, mtt_cmd` comes back as `Nom Client`, `Date Naissance`,
`Montant Commande`. Leave the language selector on *Auto-detect* to let the model infer it, or pin
it with `"language": "fr"` (`auto`, `en`, `fr`, `es`, `de`, `it`, `pt`, `nl`) when short or ambiguous
abbreviations could be read as English.

## API

```bash
curl -s localhost:8000/api/expand -H 'content-type: application/json' -d '{
  "schema_text": "emp_id, emp_nm, dept_cd, doj, sal_amt",
  "table_name": "Emp_info",
  "language": "auto",
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

`test_expander.py` covers schema parsing, the answer parser (arrow variants, unknown columns,
accented expansions) and the language instruction, without calling the LLM.
