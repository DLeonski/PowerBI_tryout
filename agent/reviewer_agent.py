import json
import anthropic
import config

REVIEWER_SYSTEM_PROMPT = """You are a Power BI dashboard quality reviewer.
You receive: the original user command, the model_spec (visuals and measures designed), and the data cleaning log.
Your job: check that the visuals match the data, DAX measures are syntactically plausible, and cleaning decisions were sensible.
Reply with a JSON object: {"approved": true/false, "feedback": "...brief explanation..."}
Be concise. Only block (approved: false) for clear errors (wrong visual type, obviously broken DAX, missing key visual).
"""


def review(command: str, model_spec: dict, decision_log: list[str]) -> dict:
    """
    Run a separate Claude session to review the agent's decisions.
    Returns {"approved": bool, "feedback": str}
    """
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    user_message = f"""
User command: {command}

Cleaning decisions:
{chr(10).join(f'- {entry}' for entry in decision_log)}

Model spec:
{json.dumps(model_spec, indent=2)}

Review and reply with JSON: {{"approved": true/false, "feedback": "..."}}
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=REVIEWER_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    text = response.content[0].text.strip()
    # Extract JSON from response (may be wrapped in markdown code block)
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # If Claude didn't return valid JSON, treat as approved with note
        return {"approved": True, "feedback": text}
