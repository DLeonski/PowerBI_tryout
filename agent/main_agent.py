import json
from datetime import datetime
from pathlib import Path

import anthropic

import config
from agent.tools import TOOL_DEFINITIONS, dispatch_tool, _state
from agent.reviewer_agent import review

SYSTEM_PROMPT = """You are an autonomous Power BI engineer. You receive a natural language command and a CSV file path.
Your job is to produce a Power BI dashboard (.pbix) and a decision report (.md).

You MUST call tools in this order:
1. profile_data — understand the data structure and column types
2. classify_domain — pass the full profile dict returned by profile_data; note the returned domain and matched_columns
3. load_skills — pass domain from classify_domain result AND viz-routing chart types you plan to use. Analyze viz-routing to pick chart types.
   If the domain skill was loaded (e.g. retail), follow its KPI hierarchy (Steps 2-4) to select which visuals to build.
   If domain is generic, use base skills only.
4. clean_data — clean based on profile and general-rules skill. Do NOT remove outliers — they may represent legitimate high-value events.
5. design_model — design visuals and DAX measures based on data profile and loaded skills.
   If retail domain: follow the retail skill's mandatory visuals (timeline, leaderboard, breakdown, profitability matrix, discount impact chart).
   Column names in visuals must exactly match the cleaned data columns.
6. load_skills with include_design=true — load the dashboard color & layout placement skill (zones, color system, typography). Apply these rules to finalize visual positions, colors, and sizes in your model_spec before generating.
7. generate_pbix — generate the .pbix file
8. write_report — write the decision report

Use the output_dir provided in the user message for all file outputs.
When calling design_model, pass a complete model_spec with: report_title, data_source_path (the cleaned data path), visuals (list of dicts), measures (list of {name, expression}).

Each visual dict MUST be a structured object (not a string) with these keys:
- type: one of lineChart, barChart, kpiCard, pieChart, tableEx, scatterPlot
- title: display title
- position: {x, y} in pixels
- width, height: in pixels
- For lineChart/scatterPlot: x_column (date/text column name), y_column (numeric column name)
- For barChart: category_column (text column name), value_column (numeric column name)
- For pieChart: category_column (text column name), value_column (numeric column name)
- For kpiCard: value_column (numeric column name)
- For tableEx: columns (list of column names to show)

Column names must exactly match column names in the data profile.
After loading the design skill in step 6, update visual positions and color assignments in the model_spec to comply with the 3-zone layout and color system before calling generate_pbix.
"""


def run(command: str, csv_path: str, output_dir: str | None = None) -> dict:
    """
    Run the main agent. Returns {pbix_path, report_path, reviewer_feedback}.
    Raises RuntimeError if reviewer rejects after 2 iterations.
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = output_dir or str(Path(config.OUTPUT_DIR) / ts)

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    user_message = f"""Command: {command}
CSV file: {csv_path}
Output directory: {output_dir}
"""

    messages = [{"role": "user", "content": user_message}]

    # Tool-use loop
    for _ in range(20):  # max 20 tool calls to prevent runaway loops
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOL_DEFINITIONS,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            break

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = dispatch_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })
            messages.append({"role": "user", "content": tool_results})

    # Reviewer loop (max 2 iterations)
    model_spec = _state.get("model_spec", {})
    cleaning_log = _state.get("cleaning_log", [])

    review_result = {"approved": True, "feedback": ""}
    for attempt in range(2):
        review_result = review(command, model_spec, cleaning_log)

        if review_result.get("approved", True):
            break

        if attempt == 1:
            # Write diagnostic report instead of .pbix
            error_report = Path(output_dir) / "review_failed.md"
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            error_report.write_text(
                f"# Review Failed\n\nFeedback after 2 attempts:\n{review_result['feedback']}",
                encoding="utf-8",
            )
            raise RuntimeError(
                f"Reviewer rejected output after 2 attempts. See {error_report}"
            )

        # Feed reviewer feedback back into agent for one more pass
        messages.append({
            "role": "user",
            "content": f"Reviewer feedback: {review_result['feedback']}. Please redesign the model_spec and regenerate.",
        })

        # Re-run tool loop
        for _ in range(10):
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
                messages=messages,
            )
            messages.append({"role": "assistant", "content": response.content})
            if response.stop_reason == "end_turn":
                break
            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = dispatch_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result),
                        })
                messages.append({"role": "user", "content": tool_results})
        model_spec = _state.get("model_spec", {})

    return {
        "pbix_path": _state.get("pbix_path"),
        "report_path": _state.get("report_path"),
        "reviewer_feedback": review_result.get("feedback", ""),
    }
