"""Checks for project 12. Run from the project folder: python -m pytest spec_tests -v"""

import inspect
import re

import pytest
from fastapi.testclient import TestClient

from expenses import api
from expenses.api import create_app

LUNCH = {"amount": 12.5, "category": "food", "description": "Lunch", "spent_on": "2026-10-18"}


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test.db"


@pytest.fixture
def client(db_path):
    with TestClient(create_app(db_path)) as client:
        yield client


@pytest.fixture
def october(client):
    client.post("/categories", json={"name": "food", "monthly_budget": 300})
    client.post("/categories", json={"name": "rent", "monthly_budget": 1000})
    client.post("/categories", json={"name": "travel", "monthly_budget": 200})
    for amount, category, description, day in [
        (250, "food", "Groceries", "2026-10-03"),
        (80, "food", "Restaurant", "2026-10-20"),
        (1000, "rent", "October rent", "2026-10-01"),
        (20, "fun", "Cinema", "2026-10-11"),
        (500, "food", "Big September shop", "2026-09-28"),
    ]:
        response = client.post(
            "/expenses",
            json={"amount": amount, "category": category, "description": description, "spent_on": day},
        )
        assert response.status_code == 201, response.text
    return client


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


class TestCategories:
    def test_create(self, client):
        response = client.post("/categories", json={"name": "food", "monthly_budget": 300})
        assert response.status_code == 201
        body = response.json()
        assert isinstance(body["id"], int)
        assert body["name"] == "food" and body["monthly_budget"] == 300

    def test_budget_is_optional(self, client):
        response = client.post("/categories", json={"name": "fun"})
        assert response.status_code == 201
        assert response.json()["monthly_budget"] is None

    def test_duplicate(self, client):
        client.post("/categories", json={"name": "food"})
        response = client.post("/categories", json={"name": "food"})
        assert response.status_code == 409
        assert "detail" in response.json()

    def test_list_sorted(self, client):
        for name in ["rent", "food", "travel"]:
            client.post("/categories", json={"name": name})
        response = client.get("/categories")
        assert response.status_code == 200
        assert [c["name"] for c in response.json()] == ["food", "rent", "travel"]


class TestExpenses:
    def test_create(self, client):
        response = client.post("/expenses", json=LUNCH)
        assert response.status_code == 201
        body = response.json()
        assert isinstance(body["id"], int)
        assert {k: body[k] for k in LUNCH} == LUNCH

    def test_description_is_optional(self, client):
        body = {k: v for k, v in LUNCH.items() if k != "description"}
        response = client.post("/expenses", json=body)
        assert response.status_code == 201
        assert response.json()["description"] == ""

    def test_get(self, client):
        created = client.post("/expenses", json=LUNCH).json()
        response = client.get(f"/expenses/{created['id']}")
        assert response.status_code == 200
        assert response.json() == created

    def test_get_missing(self, client):
        response = client.get("/expenses/9999")
        assert response.status_code == 404
        assert "detail" in response.json()

    @pytest.mark.parametrize(
        "changes",
        [
            {"amount": 0},
            {"amount": -5},
            {"amount": "abc"},
            {"spent_on": "2026-02-30"},
            {"spent_on": "yesterday"},
        ],
    )
    def test_invalid_body(self, client, changes):
        response = client.post("/expenses", json={**LUNCH, **changes})
        assert response.status_code == 422

    @pytest.mark.parametrize("missing", ["amount", "category", "spent_on"])
    def test_missing_field(self, client, missing):
        body = {k: v for k, v in LUNCH.items() if k != missing}
        assert client.post("/expenses", json=body).status_code == 422

    def test_list_and_filters(self, october):
        everything = october.get("/expenses").json()
        assert len(everything) == 5

        response = october.get("/expenses", params={"month": "2026-10"})
        assert response.status_code == 200
        assert [e["description"] for e in response.json()] == [
            "October rent", "Groceries", "Cinema", "Restaurant",
        ]

        food = october.get("/expenses", params={"category": "food"}).json()
        assert [e["description"] for e in food] == ["Big September shop", "Groceries", "Restaurant"]

        both = october.get("/expenses", params={"month": "2026-09", "category": "food"}).json()
        assert [e["description"] for e in both] == ["Big September shop"]

    @pytest.mark.parametrize("month", ["Oct", "2026-13", "2026-1"])
    def test_list_bad_month(self, client, month):
        assert client.get("/expenses", params={"month": month}).status_code == 422

    def test_patch_changes_only_given_fields(self, client):
        created = client.post("/expenses", json=LUNCH).json()
        response = client.patch(f"/expenses/{created['id']}", json={"amount": 15})
        assert response.status_code == 200
        body = response.json()
        assert body["amount"] == 15
        assert body["description"] == "Lunch" and body["spent_on"] == "2026-10-18"
        assert client.get(f"/expenses/{created['id']}").json()["amount"] == 15

    def test_patch_validates(self, client):
        created = client.post("/expenses", json=LUNCH).json()
        assert client.patch(f"/expenses/{created['id']}", json={"amount": -1}).status_code == 422

    def test_patch_missing(self, client):
        assert client.patch("/expenses/9999", json={"amount": 15}).status_code == 404

    def test_delete(self, client):
        created = client.post("/expenses", json=LUNCH).json()
        response = client.delete(f"/expenses/{created['id']}")
        assert response.status_code == 204
        assert response.content == b""
        assert client.get(f"/expenses/{created['id']}").status_code == 404
        assert client.delete(f"/expenses/{created['id']}").status_code == 404

    def test_injection_is_stored_as_text(self, client):
        text = "x'; DROP TABLE expenses; --"
        client.post("/expenses", json={**LUNCH, "description": text, "category": text})
        listed = client.get("/expenses").json()
        assert listed[0]["description"] == text and listed[0]["category"] == text


class TestSummary:
    def test_summary(self, october):
        response = october.get("/summary", params={"month": "2026-10"})
        assert response.status_code == 200
        rows = {r["category"]: r for r in response.json()}
        assert list(rows) == ["food", "fun", "rent", "travel"]
        assert rows["food"] == {
            "category": "food", "spent": 330, "budget": 300, "remaining": -30, "over_budget": True,
        }
        assert rows["fun"]["budget"] is None and rows["fun"]["remaining"] is None
        assert rows["travel"]["spent"] == 0 and rows["travel"]["over_budget"] is False

    @pytest.mark.parametrize("params", [{}, {"month": "October"}])
    def test_month_is_required_and_validated(self, client, params):
        assert client.get("/summary", params=params).status_code == 422


def test_data_persists_between_apps(db_path):
    with TestClient(create_app(db_path)) as first:
        first.post("/expenses", json=LUNCH)
    with TestClient(create_app(db_path)) as second:
        assert [e["description"] for e in second.get("/expenses").json()] == ["Lunch"]


def test_db_path_from_environment(tmp_path, monkeypatch):
    path = tmp_path / "from-env.db"
    monkeypatch.setenv("EXPENSES_DB", str(path))
    with TestClient(create_app()) as client:
        client.post("/expenses", json=LUNCH)
    assert path.exists()


def test_openapi_docs_list_every_route(client):
    paths = client.get("/openapi.json").json()["paths"]
    for path in ["/health", "/categories", "/expenses", "/summary"]:
        assert path in paths, path
    assert any(re.fullmatch(r"/expenses/\{\w+\}", p) for p in paths), "/expenses/{id}"


def test_api_has_no_sql():
    source = inspect.getsource(api)
    assert "sqlite3" not in source and ".execute(" not in source, "Keep SQL in repository.py"
