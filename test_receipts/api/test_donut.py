import os
import pytest

from pathlib import Path
from prepline_receipts.donut import generate_outputs, clean_fields, extract_fields, select_fields
from unstructured_api_tools.pipelines.api_conventions import get_pipeline_path

DIRECTORY = Path(__file__).absolute().parent
SAMPLE_DOCS_DIRECTORY = os.path.join(DIRECTORY, "..", "..", "sample-docs")
COMMENTS_ROUTE = get_pipeline_path("receipts", pipeline_family="receipts", semver="0.1.0")

print("DIRECTORY: ", DIRECTORY)
print("SAMPLE_DOCS_DIRECTORY: ", SAMPLE_DOCS_DIRECTORY)
print("COMMENTS_ROUTE: ", COMMENTS_ROUTE)


@pytest.fixture
def expected_extracted_fields():
    return (
        ["TransactionTime", "TransactionDate", "Total", "Tax", "Subtotal", "Menu", "Items"],
        ["TotalPrice", "Quantity", "Price", "Name", "TotalPrice", "Quantity", "Price", "Name"],
    )


@pytest.fixture
def expected_selected_fields_receipt():
    return {"Total": "170.00", "Tax": "0.00", "Subtotal": "170.00"}


@pytest.fixture
def expected_filtered_structured_receipt():
    return {
        "TransactionTime": "2:47:14",
        "TransactionDate": "02/01/2019",
        "Total": "170.00",
        "Tax": "0.00",
        "Subtotal": "170.00",
        "Menu": [
            {"Name": "", "Price": "170.00", "Quantity": "1", "TotalPrice": "170.00"},
            {"Name": "805", "Price": "", "Quantity": "1", "TotalPrice": "170.00"},
        ],
        "Items": "",
    }


def test_not_implemented_model_generate_outputs():
    image, filename = "", ""
    with pytest.raises(NotImplementedError):
        generate_outputs(image, filename)


def test_empty_receipt_model_generate_outputs():
    image, filename = "", ""
    with pytest.raises(ValueError):
        generate_outputs(model="donut", image=image, filename=filename)


def test_extracted_fields_content(expected_extracted_fields):
    filename = os.path.join(SAMPLE_DOCS_DIRECTORY, "SROIE-test-4/X00016469671.jpg")
    parsed_doc = generate_outputs(model="donut", image=open(filename, "rb"))
    extracted_fields = extract_fields(parsed_doc)
    assert extracted_fields == expected_extracted_fields


def test_filtered_fields_content(expected_filtered_structured_receipt):
    filename = os.path.join(SAMPLE_DOCS_DIRECTORY, "SROIE-test-4/X00016469671.jpg")
    parsed_doc = generate_outputs(model="donut", image=open(filename, "rb"))
    parsed_doc = clean_fields(parsed_doc, "price_rule")
    assert parsed_doc.keys() == expected_filtered_structured_receipt.keys()


def test_selected_fields_content_api(expected_selected_fields_receipt):
    filename = os.path.join(SAMPLE_DOCS_DIRECTORY, "SROIE-test-4/X00016469671.jpg")
    selected_fields = ["Price", "Quantity", "Subtotal", "Tax", "Total", "TotalPrice"]
    parsed_doc = generate_outputs(model="donut", filename=filename)
    selected_fields_receipt = select_fields(parsed_doc, selected_fields)
    assert selected_fields_receipt == expected_selected_fields_receipt
