"""Token-level expansion of abbreviated column names via an OpenAI chat model.

The prompt and the ``token -> expansion`` output contract follow the Columbo
paper's column-expansion stage (https://github.com/anhaidgroup/columbo).
"""

import re

from openai import AsyncOpenAI

SYSTEM_PROMPT = (
    "You are a helpful assistant, answer the question from the user and reply in the same format."
)

GUIDELINES = """Your task is to expand abbreviated column names into full-form phrases.
You should return the tokens of each column name and their associated expansions.
First reason step by step and then return your final answer.
Follow the guidelines below when you expand:
1. Expand all abbreviations in the column names.
2. Expand chemical symbols and units of measure to their full names.
3. Do not expand or mutate numbers.
4. Do not add extra words or explanations.
5. Maintain the original order of tokens in the expansion.
6. The tokens should be as concise and simple as possible.
7. Only provide 1 expansion for each token, even if you are uncertain, output the most possible one.
8. If the token is not abbreviated, the expansion should be itself, do not paraphrase.
"""

# Language of the column names, and therefore of the expansions.
LANGUAGES = {
    "auto": "",
    "en": "English",
    "fr": "French",
    "es": "Spanish",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
}

AUTO_LANGUAGE_RULE = (
    "9. The column names may be in any language. Detect the language of each column name "
    "and write its expansion in that same language, using the spelling and accents native "
    "to it. Never translate into English.\n"
)

FIXED_LANGUAGE_RULE = (
    "9. The column names are in {language}. Write every expansion in {language}, using the "
    "spelling and accents native to it. Never translate into another language.\n"
)

DEMOS = """[Question]
As abbreviations of column names from a table named Prchs_info, c_name | pCd | dt stand for
[Answer]
### Reasoning
The table "Prchs_info" is about purchase information.
### Final Answer
c_name: c -> Customer, name -> Name
pCd: p -> Product, Cd -> Code
dt: dt -> Date

[Question]
As abbreviations of column names from a table named AirQ_data, stn_id | pm25_lvl | temp_C stand for
[Answer]
### Reasoning
The table "AirQ_data" is about air quality measurements.
### Final Answer
stn_id: stn -> Station, id -> Identifier
pm25_lvl: pm25 -> Particulate Matter 2.5, lvl -> Level
temp_C: temp -> Temperature, C -> Celsius

[Question]
As abbreviations of column names from a table named Cli_infos, nom_cli | dt_nais | cp | mtt_cmd stand for
[Answer]
### Reasoning
The table "Cli_infos" is about customer information, and the column names are in French, so the expansions are in French.
### Final Answer
nom_cli: nom -> Nom, cli -> Client
dt_nais: dt -> Date, nais -> Naissance
cp: cp -> Code Postal
mtt_cmd: mtt -> Montant, cmd -> Commande
"""

RULE_PATTERN = r"([\w/^%():#/\.\-\s]+?)\s*(?:->|→)\s*([^→]+?)(?=(?:,\s*[\w/^%():#/\.\-\s]+?\s*(?:->|→)|$))"


def language_rule(language: str) -> str:
    name = LANGUAGES.get(language.strip().lower(), "")
    if not name:
        return AUTO_LANGUAGE_RULE
    return FIXED_LANGUAGE_RULE.format(language=name)


def build_prompt(
    table_name: str,
    columns: list[str],
    context: str = "",
    language: str = "auto",
) -> list[dict]:
    table = table_name.strip() or "unknown_table"
    query = GUIDELINES + language_rule(language)
    if context.strip():
        query += f"\nAdditional context about the dataset: {context.strip()}\n"
    query += "\n" + DEMOS
    query += (
        f"\n[Question]\nAs abbreviations of column names from a table named {table}, "
        f"{' | '.join(columns)} stand for\n[Answer]\n"
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query},
    ]


def parse_answer(raw: str, columns: list[str]) -> list[dict]:
    """Map each requested column to its token expansions, in request order."""
    body = raw.split("### Final Answer")[-1]
    by_column: dict[str, str] = {}
    for line in body.splitlines():
        line = line.strip().lstrip("#").strip()
        if not line or ":" not in line:
            continue
        name, _, rules = line.partition(":")
        by_column[name.strip().strip("*` ").lower()] = rules

    results = []
    for column in columns:
        rules = by_column.get(column.strip().lower(), "")
        tokens = [
            {"token": token.strip(), "expansion": expansion.strip()}
            for token, expansion in re.findall(RULE_PATTERN, rules)
        ]
        results.append(
            {
                "column": column,
                "tokens": tokens,
                "expansion": " ".join(t["expansion"] for t in tokens),
            }
        )
    return results


async def expand_columns(
    api_key: str,
    table_name: str,
    columns: list[str],
    context: str = "",
    language: str = "auto",
    model: str = "gpt-4o",
    temperature: float = 0.0,
) -> tuple[list[dict], str]:
    client = AsyncOpenAI(api_key=api_key)
    completion = await client.chat.completions.create(
        model=model,
        messages=build_prompt(table_name, columns, context, language),
        temperature=temperature,
        max_completion_tokens=4000,
    )
    raw = completion.choices[0].message.content or ""
    return parse_answer(raw, columns), raw
