from pathlib import Path

SKILLS_DIR = Path(__file__).parent

BASE_FILES = [
    SKILLS_DIR / "base" / "general-rules.md",
    SKILLS_DIR / "viz-routing.md",
]

DESIGN_SKILL_FILE = SKILLS_DIR / "base" / "dashboard-design.md"


def load_skills(
    chart_types: list[str] | None = None,
    include_design: bool = False,
    domain: str | None = None,
) -> str:
    """Return concatenated skill text. Base skills always included.
    chart_types: list of viz skill names e.g. ['line-chart', 'bar-chart']
    include_design: if True, append the dashboard color & layout placement skill
    domain: domain name e.g. 'retail'. Loads skills/domains/<domain>.md if it exists.
            Pass None or 'generic' to skip domain skill.
    """
    parts = []
    for path in BASE_FILES:
        if path.exists():
            parts.append(f"## {path.stem}\n\n{path.read_text(encoding='utf-8')}")

    if domain and domain != "generic":
        domain_path = SKILLS_DIR / "domains" / f"{domain}.md"
        if domain_path.exists():
            parts.append(f"## domain-{domain}\n\n{domain_path.read_text(encoding='utf-8')}")

    for chart_type in (chart_types or []):
        path = SKILLS_DIR / "viz" / f"{chart_type}.md"
        if path.exists():
            parts.append(f"## {path.stem}\n\n{path.read_text(encoding='utf-8')}")

    if include_design and DESIGN_SKILL_FILE.exists():
        parts.append(f"## {DESIGN_SKILL_FILE.stem}\n\n{DESIGN_SKILL_FILE.read_text(encoding='utf-8')}")

    return "\n\n---\n\n".join(parts)
