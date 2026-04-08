import json
import shutil
import zipfile
from pathlib import Path
from pbix.visual_templates import build_visual_container


def generate_pbix(model_spec: dict, template_path: str, output_path: str) -> None:
    """
    Generate a .pbix by cloning template and injecting visuals into Report/Layout.
    Data is NOT embedded — user must refresh data source in Power BI Desktop.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(template_path, output_path)

    # Read current layout from template
    with zipfile.ZipFile(output_path, "r") as z:
        layout_raw = z.read("Report/Layout").decode("utf-16-le")

    layout = json.loads(layout_raw)

    # Ensure at least one section exists
    if not layout.get("sections"):
        layout["sections"] = [{
            "id": 0,
            "name": "ReportSection",
            "displayName": model_spec.get("report_title", "Dashboard"),
            "visualContainers": [],
            "width": 1280,
            "height": 720,
            "config": "{}",
            "filters": "[]",
        }]

    section = layout["sections"][0]
    section["displayName"] = model_spec.get("report_title", "Dashboard")

    # Build visual containers from spec
    section["visualContainers"] = [
        build_visual_container(vis) for vis in model_spec.get("visuals", [])
    ]

    new_layout = json.dumps(layout)

    # Repack ZIP with updated Layout
    tmp_path = output_path + ".tmp"
    with zipfile.ZipFile(output_path, "r") as zin:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == "Report/Layout":
                    zout.writestr(item, new_layout.encode("utf-16-le"))
                else:
                    zout.writestr(item, zin.read(item.filename))

    Path(output_path).unlink()
    Path(tmp_path).rename(output_path)
