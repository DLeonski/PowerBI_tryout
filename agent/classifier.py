import json
import anthropic
import config

_SYSTEM_PROMPT = """You are a data domain classifier. Given a CSV data profile (column names, dtypes, sample values), identify which domain the dataset belongs to.

Known domains:
- retail: Transactional sales data. Indicators: columns for revenue/sales/amount, profit/margin, quantity/units, discount/promo, order date, product category/sub-category, customer name/id, region/geography, order id/transaction id. E-commerce, POS, marketplace exports (Shopify, WooCommerce, ERP), superstore-style CSVs all qualify.
- generic: Everything else — HR, finance, scientific, IoT, logs, etc.

Respond ONLY with a JSON object, no markdown fences, no explanation outside the JSON:
{
  "domain": "<retail|generic>",
  "confidence": "<high|medium|low>",
  "reasoning": "<one sentence>",
  "matched_columns": {
    "<semantic_role>": "<actual_column_name>"
  }
}

matched_columns should map semantic roles (revenue, profit, transaction_date, quantity, discount, category, sub_category, customer_name, region) to the actual column names found. Omit roles not found. Empty object {} if domain is generic."""


def classify_domain(profile: dict) -> dict:
    """Classify the dataset domain via a focused Haiku API call.

    Args:
        profile: The dict returned by profile_data (row_count, columns, ...).

    Returns:
        {domain, confidence, reasoning, matched_columns}
        Falls back to {domain: 'generic', confidence: 'low'} on any error.
    """
    fallback = {
        "domain": "generic",
        "confidence": "low",
        "reasoning": "Classification failed — defaulting to generic.",
        "matched_columns": {},
    }

    try:
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

        # Slim down the profile to just what the classifier needs
        slim_profile = {
            "row_count": profile.get("row_count"),
            "columns": [
                {
                    "name": col["name"],
                    "dtype": col["dtype"],
                    "semantic_type": col.get("semantic_type"),
                    "unique_count": col.get("unique_count"),
                    "sample_values": col.get("sample_values", [])[:3],
                }
                for col in profile.get("columns", [])
            ],
        }

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            system=_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Classify this dataset profile:\n\n{json.dumps(slim_profile, indent=2)}",
                }
            ],
        )

        raw = response.content[0].text.strip()
        result = json.loads(raw)

        # Ensure required keys present
        for key in ("domain", "confidence", "reasoning", "matched_columns"):
            if key not in result:
                return fallback

        return result

    except Exception as e:
        fallback["reasoning"] = f"Classification error: {e}"
        return fallback
