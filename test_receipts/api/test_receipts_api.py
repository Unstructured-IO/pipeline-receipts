import os
import pytest
import json

from pathlib import Path
from fastapi.testclient import TestClient

from prepline_receipts.api.app import app as core_app
from prepline_receipts.api.receipts import app
from unstructured_api_tools.pipelines.api_conventions import get_pipeline_path

DIRECTORY = Path(__file__).absolute().parent
SAMPLE_DOCS_DIRECTORY = os.path.join(DIRECTORY, "..", "..", "sample-docs")
COMMENTS_ROUTE = get_pipeline_path("receipts", pipeline_family="receipts", semver="0.1.0")

print("DIRECTORY: ", DIRECTORY)
print("SAMPLE_DOCS_DIRECTORY: ", SAMPLE_DOCS_DIRECTORY)
print("COMMENTS_ROUTE: ", COMMENTS_ROUTE)


def test_receipts_api_health_check():
    client = TestClient(app)
    response = client.get("/healthcheck")
    assert response.status_code == 200


def test_core_app_health_check():
    # NOTE(crag): switch all tests to core_app when rate limiting is removed
    client = TestClient(core_app)
    response = client.get("/healthcheck")
    assert response.status_code == 200


@pytest.fixture
def fake_structured_receipt():
    return {
        "Items": "",
        "Menu": [
            {"Name": "KINGS SAFETY", "Price": "170.00", "Quantity": "1", "TotalPrice": "170.00"},
            {"Name": "SHOES KWD 805", "Price": "None", "Quantity": "1", "TotalPrice": "170.00"},
        ],
        "Subtotal": "170.00",
        "Tax": "0.00",
        "Total": "170.00",
        "TransactionDate": "02/01/2019",
        "TransactionTime": "2:47:14",
    }


@pytest.fixture
def fake_selected_structured_receipt():
    return {"Total": "170.00", "Tax": "0.00", "Subtotal": "170.00"}


@pytest.fixture
def fake_selected_structured_receipt_alt():
    return {
        "Menu": [
            {"Name": "KINGS SAFETY", "Price": "170.00", "Quantity": "1", "TotalPrice": "170.00"},
            {"Name": "SHOES KWD 805", "Price": "None", "Quantity": "1", "TotalPrice": "170.00"},
        ]
    }


def test_fields_content_api(fake_structured_receipt):
    filename = os.path.join(SAMPLE_DOCS_DIRECTORY, "SROIE-test-4/X00016469671.jpg")
    app.state.limiter.reset()
    client = TestClient(app)
    response = client.post(
        COMMENTS_ROUTE,
        files={
            "files": (
                filename,
                open(filename, "rb"),
            )
        },
    )
    response_content = json.loads(response.content.decode("utf-8"))["parsed_doc"]
    assert response.status_code == 200
    assert response_content == fake_structured_receipt


def test_selected_fields_content_api(fake_selected_structured_receipt):
    filename = os.path.join(SAMPLE_DOCS_DIRECTORY, "SROIE-test-4/X00016469671.jpg")
    app.state.limiter.reset()
    client = TestClient(app)
    selected_fields = ["Subtotal", "Tax", "Total"]
    response = client.post(
        COMMENTS_ROUTE,
        files={
            "files": (
                filename,
                open(filename, "rb"),
            )
        },
        data={"include_fields": selected_fields},
    )
    response_content = json.loads(response.content.decode("utf-8"))["parsed_doc"]
    assert response.status_code == 200
    assert response_content == fake_selected_structured_receipt


def test_selected_fields_content_api_alt(fake_selected_structured_receipt_alt):
    filename = os.path.join(SAMPLE_DOCS_DIRECTORY, "SROIE-test-4/X00016469671.jpg")
    app.state.limiter.reset()
    client = TestClient(app)
    selected_fields = ["Menu"]
    response = client.post(
        COMMENTS_ROUTE,
        files={
            "files": (
                filename,
                open(filename, "rb"),
            )
        },
        data={"include_fields": selected_fields},
    )
    response_content = json.loads(response.content.decode("utf-8"))["parsed_doc"]
    assert response.status_code == 200
    assert response_content == fake_selected_structured_receipt_alt


def test_response_api_multi():
    filename_a = os.path.join(SAMPLE_DOCS_DIRECTORY, "SROIE-test-4/X00016469671.jpg")
    filename_b = os.path.join(SAMPLE_DOCS_DIRECTORY, "SROIE-test-4/X00016469670.jpg")
    filenames = [filename_a, filename_b]
    app.state.limiter.reset()
    client = TestClient(app)
    selected_fields = [
        "total",
        "total_price",
        "sub_total",
        "subtotal_price",
        "tax_price",
        "unitprice",
        "price",
        "creditcardprice",
    ]
    files = [("files", (filename, open(filename, "rb"), "image/jpeg")) for filename in filenames]
    response = client.post(
        COMMENTS_ROUTE,
        headers={"Accept": "multipart/mixed"},
        files=files,
        data={"include_fields": selected_fields},
    )
    assert response.status_code == 200
    assert "multipart/mixed" in response.headers["content-type"]


def test_empty_files_response_api():
    app.state.limiter.reset()
    client = TestClient(app)
    response = client.post(COMMENTS_ROUTE)
    assert response.status_code == 400


def test_filtered_fields_content_api_a():
    filename = os.path.join(SAMPLE_DOCS_DIRECTORY, "SROIE-test-4/X00016469671.jpg")
    app.state.limiter.reset()
    client = TestClient(app)
    response = client.post(
        COMMENTS_ROUTE,
        files={
            "files": (
                filename,
                open(filename, "rb"),
            )
        },
        data={"cleaning_fnc": ["price_rule"]},
    )
    assert response.status_code == 200


def test_filtered_fields_content_api_b():
    filename = os.path.join(SAMPLE_DOCS_DIRECTORY, "SROIE-test-4/X00016469671.jpg")
    app.state.limiter.reset()
    client = TestClient(app)
    response = client.post(
        COMMENTS_ROUTE,
        files={
            "files": (
                filename,
                open(filename, "rb"),
            )
        },
        data={"cleaning_fnc": ["vendor_rule"]},
    )
    assert response.status_code == 200
