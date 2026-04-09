import json
import shutil
import struct
import zipfile
from pathlib import Path
from pbix.visual_templates import build_visual_container

# Canvas dimensions (Power BI default)
_CANVAS_W = 1280
_CANVAS_H = 720
_PAD = 12

# Visual type → (zone, slot)
# zone 1 = KPI bar, zone 2 = primary analysis, zone 3 = detail/supporting
# slot: "kpi" | "left" | "right"
_TYPE_ZONE_SLOT: dict[str, tuple[int, str]] = {
    "kpiCard":    (1, "kpi"),
    "pieChart":   (2, "left"),
    "lineChart":  (2, "right"),
    "scatterPlot":(2, "right"),
    "barChart":   (3, "left"),
    "tableEx":    (3, "right"),
}


def _assign_layout(visuals: list[dict]) -> list[dict]:
    """
    Compute x/y/width/height for every visual to fill the 1280×720 canvas.

    Zone 1 — KPI bar (top, full width, 100px tall): all kpiCard visuals,
              equally wide.
    Zone 2 — Primary analysis (43% of remaining height):
              left slot 33% wide (compact/donut), right slot 67% wide (trend chart).
    Zone 3 — Detail (remaining height):
              left slot 57% wide (bar/scatter), right slot 43% wide (table).

    Visuals that don't match a known type go into zone 3 left by default.
    Multiple visuals assigned to the same slot are stacked vertically.
    """
    slots: dict[str, list[dict]] = {
        "kpi": [], "z2_left": [], "z2_right": [], "z3_left": [], "z3_right": []
    }
    for vis in visuals:
        zone, slot = _TYPE_ZONE_SLOT.get(vis.get("type", "tableEx"), (3, "left"))
        key = "kpi" if zone == 1 else f"z{zone}_{slot}"
        slots[key].append(vis)

    # Zone 1 geometry
    kpis = slots["kpi"]
    kpi_h = 100
    z1_bottom = _PAD + (kpi_h if kpis else 0) + _PAD

    # Zone 3 gets a fixed height so zone 2 fills whatever remains
    z3_h = 240
    z2_h = _CANVAS_H - z1_bottom - _PAD - z3_h - _PAD
    z3_y = z1_bottom + z2_h + _PAD

    usable_w = _CANVAS_W - 2 * _PAD  # 1256px
    z2_left_w  = round(usable_w * 0.33)
    z2_right_x = _PAD + z2_left_w + _PAD
    z2_right_w = _CANVAS_W - z2_right_x - _PAD

    z3_left_w  = round(usable_w * 0.57)
    z3_right_x = _PAD + z3_left_w + _PAD
    z3_right_w = _CANVAS_W - z3_right_x - _PAD

    def _place(vis_list: list[dict], x: int, y: int, w: int, h: int) -> list[dict]:
        """Stack visuals vertically within a slot."""
        n = len(vis_list)
        if n == 0:
            return []
        slot_h = (h - (n - 1) * _PAD) // n
        out = []
        for i, vis in enumerate(vis_list):
            vis = dict(vis)
            vis["position"] = {"x": x, "y": y + i * (slot_h + _PAD)}
            vis["width"] = w
            vis["height"] = slot_h
            out.append(vis)
        return out

    result: list[dict] = []

    # Zone 1: KPI cards — equal width, single row
    if kpis:
        n = len(kpis)
        card_w = (_CANVAS_W - (n + 1) * _PAD) // n
        for i, vis in enumerate(kpis):
            vis = dict(vis)
            vis["position"] = {"x": _PAD + i * (card_w + _PAD), "y": _PAD}
            vis["width"] = card_w
            vis["height"] = kpi_h
            result.append(vis)

    result += _place(slots["z2_left"],  _PAD,       z1_bottom, z2_left_w,  z2_h)
    result += _place(slots["z2_right"], z2_right_x, z1_bottom, z2_right_w, z2_h)
    result += _place(slots["z3_left"],  _PAD,       z3_y,      z3_left_w,  z3_h)
    result += _place(slots["z3_right"], z3_right_x, z3_y,      z3_right_w, z3_h)

    return result

# Microsoft OPC extra field (tag 0xa220) required in every local file header.
# Power BI rejects PBIX files that lack this field.
_OPC_EXTRA = bytes.fromhex("20a2180028a014000000000000000000000000000000000000000000")


def _read_local_extras(zip_path: str) -> dict[str, bytes]:
    """Return {filename: extra_bytes} from the local file headers of a ZIP."""
    extras = {}
    data = Path(zip_path).read_bytes()
    sig = b"PK\x03\x04"
    offset = 0
    while True:
        idx = data.find(sig, offset)
        if idx == -1:
            break
        fname_len = struct.unpack_from("<H", data, idx + 26)[0]
        extra_len = struct.unpack_from("<H", data, idx + 28)[0]
        fname = data[idx + 30 : idx + 30 + fname_len].decode("utf-8")
        extra = data[idx + 30 + fname_len : idx + 30 + fname_len + extra_len]
        extras[fname] = extra
        offset = idx + 4
    return extras


def _fix_central_directory(zip_path: str) -> None:
    """
    Post-process the ZIP central directory to match Power BI's expectations:
    - Remove extra fields from central dir entries (OPC extra belongs only in local headers)
    - Set external_attr to 0 (Python 3.14 forces 25165824 regardless of ZipInfo.external_attr)
    """
    data = bytearray(Path(zip_path).read_bytes())

    eocd_sig = b"PK\x05\x06"
    eocd_offset = data.rfind(eocd_sig)
    if eocd_offset == -1:
        raise ValueError("EOCD not found in ZIP")

    cd_offset = struct.unpack_from("<I", data, eocd_offset + 16)[0]

    new_cd = bytearray()
    pos = cd_offset
    while pos < eocd_offset:
        if data[pos:pos + 4] != b"PK\x01\x02":
            break
        fname_len = struct.unpack_from("<H", data, pos + 28)[0]
        extra_len = struct.unpack_from("<H", data, pos + 30)[0]
        comment_len = struct.unpack_from("<H", data, pos + 32)[0]
        total = 46 + fname_len + extra_len + comment_len

        entry = bytearray(data[pos:pos + total])
        struct.pack_into("<H", entry, 30, 0)   # zero extra_len
        struct.pack_into("<I", entry, 38, 0)   # zero external_attr

        # Write fixed header + fname only (drop extra, keep comment if any)
        new_cd += entry[:46 + fname_len]
        if comment_len:
            new_cd += entry[46 + fname_len + extra_len:]

        pos += total

    new_eocd = bytearray(data[eocd_offset:eocd_offset + 22])
    struct.pack_into("<I", new_eocd, 12, len(new_cd))   # update cd size
    struct.pack_into("<I", new_eocd, 16, cd_offset)     # cd offset unchanged

    Path(zip_path).write_bytes(bytes(data[:cd_offset]) + new_cd + new_eocd)


def generate_pbix(model_spec: dict, template_path: str, output_path: str) -> None:
    """
    Generate a .pbix by cloning template and injecting visuals into Report/Layout.
    Data is NOT embedded — user must refresh data source in Power BI Desktop.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(template_path, output_path)

    # Read current layout and settings from template
    with zipfile.ZipFile(output_path, "r") as z:
        layout_raw = z.read("Report/Layout").decode("utf-16-le")
        settings = json.loads(z.read("Settings").decode("utf-16-le"))

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

    # Derive table name from the cleaned CSV filename (Power BI default naming)
    data_source = model_spec.get("data_source_path", "")
    table_name = Path(data_source).stem if data_source else "data"

    # Assign canvas positions via layout calculator, then build visual containers
    visuals = [v for v in model_spec.get("visuals", []) if isinstance(v, dict)]
    visuals = _assign_layout(visuals)
    section["visualContainers"] = [
        build_visual_container(vis, table_name) for vis in visuals
    ]

    new_layout = json.dumps(layout, separators=(',', ':'), ensure_ascii=False)

    # Set display culture to English so axis labels, dates, and numbers render in English
    settings.setdefault("ReportSettings", {})["displayCulture"] = "en-US"
    new_settings = json.dumps(settings, separators=(',', ':'), ensure_ascii=False)

    # Repack ZIP with updated Layout and Settings, preserving the OPC extra field.
    local_extras = _read_local_extras(output_path)
    tmp_path = output_path + ".tmp"
    with zipfile.ZipFile(output_path, "r") as zin:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                item.extra = local_extras.get(item.filename, _OPC_EXTRA)
                item.external_attr = 0
                if item.filename == "Report/Layout":
                    zout.writestr(item, new_layout.encode("utf-16-le"))
                elif item.filename == "Settings":
                    zout.writestr(item, new_settings.encode("utf-16-le"))
                elif item.filename == "SecurityBindings":
                    # SecurityBindings contains a DPAPI-encrypted hash of the Layout.
                    # Modifying Layout invalidates it, so we clear it.
                    zout.writestr(item, b"")
                else:
                    zout.writestr(item, zin.read(item.filename))

    Path(output_path).unlink()
    Path(tmp_path).rename(output_path)

    # Python's zipfile copies item.extra into BOTH local headers and central directory,
    # but Power BI expects extra=0 and ext_attr=0 in the central directory.
    # Post-process the central directory to fix this.
    _fix_central_directory(output_path)
