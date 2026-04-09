import pytest
from unittest.mock import MagicMock, patch
from agent.classifier import classify_domain

RETAIL_PROFILE = {
    "row_count": 20,
    "columns": [
        {"name": "Order ID", "dtype": "object", "semantic_type": "categorical", "unique_count": 20},
        {"name": "Order Date", "dtype": "datetime64[ns]", "semantic_type": "date", "unique_count": 15},
        {"name": "Sales", "dtype": "float64", "semantic_type": "numeric_continuous", "unique_count": 20},
        {"name": "Profit", "dtype": "float64", "semantic_type": "numeric_continuous", "unique_count": 20},
        {"name": "Quantity", "dtype": "int64", "semantic_type": "numeric_continuous", "unique_count": 8},
        {"name": "Discount", "dtype": "float64", "semantic_type": "numeric_continuous", "unique_count": 5},
        {"name": "Category", "dtype": "object", "semantic_type": "categorical", "unique_count": 3},
        {"name": "Sub-Category", "dtype": "object", "semantic_type": "categorical", "unique_count": 17},
        {"name": "Region", "dtype": "object", "semantic_type": "categorical", "unique_count": 4},
        {"name": "Customer Name", "dtype": "object", "semantic_type": "text", "unique_count": 18},
    ],
    "has_date_column": True,
    "has_numeric_columns": True,
    "has_categorical_columns": True,
}

GENERIC_PROFILE = {
    "row_count": 20,
    "columns": [
        {"name": "employee_id", "dtype": "int64", "semantic_type": "numeric_continuous", "unique_count": 20},
        {"name": "department", "dtype": "object", "semantic_type": "categorical", "unique_count": 5},
        {"name": "salary", "dtype": "float64", "semantic_type": "numeric_continuous", "unique_count": 18},
        {"name": "hire_date", "dtype": "datetime64[ns]", "semantic_type": "date", "unique_count": 15},
    ],
    "has_date_column": True,
    "has_numeric_columns": True,
    "has_categorical_columns": True,
}


def _make_mock_response(domain: str, confidence: str, reasoning: str, matched: dict):
    """Build a mock anthropic response with the classifier JSON."""
    import json
    payload = json.dumps({
        "domain": domain,
        "confidence": confidence,
        "reasoning": reasoning,
        "matched_columns": matched,
    })
    mock_content = MagicMock()
    mock_content.text = payload
    mock_response = MagicMock()
    mock_response.content = [mock_content]
    return mock_response


@patch("agent.classifier.anthropic.Anthropic")
def test_retail_profile_returns_retail_domain(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_client.messages.create.return_value = _make_mock_response(
        domain="retail",
        confidence="high",
        reasoning="Sales, Profit, Order Date, Category, Sub-Category detected",
        matched={"revenue": "Sales", "profit": "Profit", "transaction_date": "Order Date"},
    )

    result = classify_domain(RETAIL_PROFILE)

    assert result["domain"] == "retail"
    assert result["confidence"] == "high"
    assert "matched_columns" in result
    assert "reasoning" in result


@patch("agent.classifier.anthropic.Anthropic")
def test_generic_profile_returns_generic_domain(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_client.messages.create.return_value = _make_mock_response(
        domain="generic",
        confidence="high",
        reasoning="No retail indicators detected",
        matched={},
    )

    result = classify_domain(GENERIC_PROFILE)

    assert result["domain"] == "generic"


@patch("agent.classifier.anthropic.Anthropic")
def test_api_error_falls_back_to_generic(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_client.messages.create.side_effect = Exception("API timeout")

    result = classify_domain(RETAIL_PROFILE)

    assert result["domain"] == "generic"
    assert result["confidence"] == "low"
    assert "error" in result["reasoning"].lower()


@patch("agent.classifier.anthropic.Anthropic")
def test_malformed_json_falls_back_to_generic(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_content = MagicMock()
    mock_content.text = "not valid json at all"
    mock_response = MagicMock()
    mock_response.content = [mock_content]
    mock_client.messages.create.return_value = mock_response

    result = classify_domain(RETAIL_PROFILE)

    assert result["domain"] == "generic"
    assert result["confidence"] == "low"
