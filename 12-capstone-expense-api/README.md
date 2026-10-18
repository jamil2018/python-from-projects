# 12 · Capstone: Expense API

Turn your project 10 expense tracker into a **web API** that a browser, a phone app, or another program could use. You'll reuse your repository and service layers unchanged and add an HTTP layer on top.

**Builds on:** 10 (repository, service, tests), 09 (HTTP and JSON), 11 (async).

## Concepts
- HTTP from the server side: routes, methods (`GET`, `POST`, `PATCH`, `DELETE`), status codes, JSON bodies
- [FastAPI](https://fastapi.tiangolo.com/): path and query parameters, request bodies, `HTTPException`
- Pydantic models for validating input and shaping output
- Dependency injection with `Depends` (one repository per request)
- Layered architecture: **routes** call the **service**, which calls the **repository**
- Automatic API docs (OpenAPI / Swagger UI)
- Integration tests with `fastapi.testclient.TestClient`
- Running an ASGI server with `uvicorn`

## Setup
```powershell
cd 12-capstone-expense-api
python -m venv .venv; .venv\Scripts\Activate.ps1
pip install fastapi uvicorn httpx pytest
```
Copy `pyproject.toml` and `src/expenses/` from project 10 as your starting point. Don't redesign them. If something has to change, ask yourself whether the change belongs in the HTTP layer instead.

## Project layout
```
12-capstone-expense-api/
  pyproject.toml
  src/expenses/
    __init__.py
    models.py
    repository.py
    service.py
    cli.py           # still works
    api.py           # NEW: FastAPI app factory and routes
    schemas.py       # NEW: Pydantic request/response models
  tests/
```

## Core requirements
`api.py` provides `create_app(db_path=None) -> FastAPI`. If `db_path` is `None`, it uses the `EXPENSES_DB` environment variable, falling back to `~/.expenses.db`.

| Method & path | Success | Errors |
|---------------|---------|--------|
| `GET /health` | `200` `{"status": "ok"}` | |
| `GET /categories` | `200` list, sorted by name | |
| `POST /categories` | `201` the new category | `409` duplicate name, `422` invalid body |
| `GET /expenses?month=YYYY-MM&category=food` | `200` list (both filters optional) | `422` bad month |
| `POST /expenses` | `201` the new expense, including its `id` | `422` invalid body |
| `GET /expenses/{id}` | `200` the expense | `404` |
| `PATCH /expenses/{id}` | `200` the updated expense. Only the fields sent change. | `404`, `422` |
| `DELETE /expenses/{id}` | `204` with an empty body | `404` |
| `GET /summary?month=YYYY-MM` | `200` list of per-category rows | `422` missing or bad month |

JSON shapes:
```json
// category
{"id": 1, "name": "food", "monthly_budget": 300.0}

// expense (POST body has everything except id; description is optional and defaults to "")
{"id": 7, "amount": 12.5, "category": "food", "description": "Lunch", "spent_on": "2026-10-18"}

// summary row
{"category": "food", "spent": 330.0, "budget": 300.0, "remaining": -30.0, "over_budget": true}
```

Rules:
1. `amount` must be greater than 0, and `spent_on` must be a real date. Let Pydantic enforce this (`Field(gt=0)`, `datetime.date`).
2. Error responses use FastAPI's standard shape: `{"detail": "..."}`.
3. Route functions contain no SQL and no business rules. They translate between HTTP and your service and repository.
4. Each request gets its own repository through a dependency that closes it afterwards. Hint: a generator dependency with `yield`. SQLite connections can't be shared across threads by default, and FastAPI may run your routes in a thread pool.

Run it:
```powershell
$env:EXPENSES_DB = "dev.db"
uvicorn --factory expenses.api:create_app --reload --app-dir src
```
Then open http://127.0.0.1:8000/docs. FastAPI generated an interactive page for every endpoint, and you can try them all from there.

## Done when
- [ ] Every row of the table above works, including the error codes
- [ ] `api.py` contains no SQL
- [ ] The project 10 CLI still works on the same database
- [ ] Your own integration tests in `tests/` use `TestClient` and a temporary database
- [ ] `/docs` shows every endpoint with its request and response models

## Stretch goals
- Pagination: `GET /expenses?limit=20&offset=40`, with the total count in an `X-Total-Count` header.
- API keys: require an `X-API-Key` header and return `401` without it. Write it as a dependency so every route gets it.
- A tiny frontend: one `index.html` served by FastAPI that lists expenses and has an "add" form using `fetch()`.
- `GET /export.csv?month=...` returns a CSV download (`StreamingResponse`).
- Package it with Docker: write a `Dockerfile` and run the API in a container.

## Automated checks
The checks in `spec_tests/` call `create_app(tmp_path / "test.db")` and talk to your app through `TestClient`. No real server or real database is used. You need `httpx` installed for `TestClient` to work.

```powershell
python -m pytest spec_tests -v
```

## Reflect
Count the lines you changed in `repository.py` and `service.py` to build this. If the answer is "almost none", your layering in project 10 paid off. Where did you put validation (Pydantic, service, or repository), and why there?
