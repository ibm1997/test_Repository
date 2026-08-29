import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import APIError, AuthenticationError
from pydantic import BaseModel, Field

from expander import expand_columns

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Columbo mini", description="Expand abbreviated column names")


class ExpandRequest(BaseModel):
    schema_text: str = Field(..., description="Column names, comma/newline separated")
    table_name: str = ""
    context: str = ""
    api_key: str = ""
    model: str = "gpt-4o"


class ColumnResult(BaseModel):
    column: str
    tokens: list[dict]
    expansion: str


class ExpandResponse(BaseModel):
    table_name: str
    results: list[ColumnResult]
    raw: str


def parse_schema(schema_text: str) -> list[str]:
    parts = [p.strip() for chunk in schema_text.splitlines() for p in chunk.split(",")]
    return [p for p in parts if p]


@app.post("/api/expand", response_model=ExpandResponse)
async def expand(req: ExpandRequest) -> ExpandResponse:
    columns = parse_schema(req.schema_text)
    if not columns:
        raise HTTPException(status_code=400, detail="No column names found in the schema.")
    api_key = req.api_key.strip() or os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=400, detail="An LLM API key is required.")

    try:
        results, raw = await expand_columns(
            api_key=api_key,
            table_name=req.table_name,
            columns=columns,
            context=req.context,
            model=req.model,
        )
    except AuthenticationError:
        raise HTTPException(status_code=401, detail="The API key was rejected by the provider.")
    except APIError as exc:
        raise HTTPException(status_code=502, detail=f"LLM call failed: {exc.message}")

    return ExpandResponse(table_name=req.table_name, results=results, raw=raw)


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
