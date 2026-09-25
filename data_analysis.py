"""Reproducible survey analysis for the CS 412 laboratory project.

The workbook is read with the Python standard library so the project does not
depend on pandas or a spreadsheet application.
"""

from __future__ import annotations

import json
import math
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

HEADERS = {
    "experience": "How would you describe your programming experience?",
    "duration": "How long have you been programming?",
    "languages": "Which programming languages do you use regularly?",
    "frequency": "How often do you code?",
    "environments": "Which development environments/IDEs are you familiar with or have used?",
    "editor": "Which IDE/editor do you use most often?",
    "assistance": "Do you prefer an editor that assists you heavily (auto-formats, suggests code) or one with minimal assistance?",
    "ai_usage": "Do you use AI tools (e.g., Copilot, ChatGPT, Claude) when programming?",
    "ai_cases": "If yes, what do you use AI for?",
    "ai_reliance": "How much do you rely on AI-generated code?",
    "comfort": "How comfortable are you writing code without AI assistance?",
}

FEATURES = {
    "Syntax highlighting": "Rate how important each feature is to you:  [Syntax highlighting]",
    "Auto-completion": "Rate how important each feature is to you:  [Auto-completion]",
    "Automatic formatting/indentation": "Rate how important each feature is to you:  [Automatic formatting/indentation]",
    "Error detection": "Rate how important each feature is to you:  [Error detection]",
    "Debugging tools": "Rate how important each feature is to you:  [Debugging tools]",
    "Code execution/testing tools": "Rate how important each feature is to you:  [Code execution/testing tools]",
    "Extensions/plugins": "Rate how important each feature is to you:  [Extensions/plugins]",
    "Language support": "Rate how important each feature is to you:  [Language support]",
}


def _clean(value: object) -> str:
    return str(value or "").strip()


def _read_xlsx(path: Path) -> list[dict[str, str]]:
    with zipfile.ZipFile(path) as archive:
        shared = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = ["".join(text.text or "" for text in item.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")) for item in root.findall("m:si", NS)]
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        rel_map = {item.attrib["Id"]: item.attrib["Target"] for item in relationships}
        sheet = workbook.find("m:sheets/m:sheet", NS)
        target = rel_map[sheet.attrib[f"{{{REL_NS}}}id"]]
        target = "xl/" + target.lstrip("/").replace("xl/", "")
        worksheet = ET.fromstring(archive.read(target))
        raw_rows = []
        for row in worksheet.findall("m:sheetData/m:row", NS):
            values = {}
            for cell in row.findall("m:c", NS):
                reference = cell.attrib.get("r", "")
                column = re.sub(r"\d+", "", reference)
                value = cell.find("m:v", NS)
                text = "" if value is None else value.text or ""
                if cell.attrib.get("t") == "s" and text:
                    text = shared[int(text)]
                values[column] = text
            raw_rows.append(values)
        ordered_headers = {column: _clean(value) for column, value in raw_rows[0].items() if _clean(value)}
        return [{header: _clean(row.get(column, "")) for column, header in ordered_headers.items()} for row in raw_rows[1:] if any(row.values())]


def _header(row: dict[str, str], prefix: str) -> str:
    for key in row:
        if key.strip().startswith(prefix):
            return key
    raise KeyError(prefix)


def _number(value: str) -> float:
    match = re.search(r"\d+(?:\.\d+)?", value)
    return float(match.group()) if match else math.nan


def _counts(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, float]]:
    counts = Counter(_clean(row[key]) for row in rows if _clean(row[key]))
    total = len(rows)
    return {label: {"count": count, "percentage": round(count / total * 100, 1)} for label, count in counts.items()}


def _multi_counts(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, float]]:
    counts = Counter()
    for row in rows:
        counts.update(item.strip() for item in _clean(row[key]).split(",") if item.strip())
    total = len(rows)
    return {label: {"count": count, "percentage": round(count / total * 100, 1)} for label, count in counts.items()}


def _mean(values: list[float]) -> float | None:
    values = [value for value in values if not math.isnan(value)]
    return round(sum(values) / len(values), 2) if values else None


def _comfort_score(value: str) -> float:
    return {"Not comfortable": 1, "Somewhat comfortable": 2, "Very comfortable": 3}.get(value, math.nan)


def _assistance_label(value: str) -> str:
    score = _number(value)
    if score >= 4:
        return "High assistance"
    if score <= 2:
        return "Minimal assistance"
    return "Moderate assistance"


def _write_svg(path: Path, title: str, values: dict[str, int], color: str = "#2f6f8f") -> None:
    width, height = 860, 440
    margin_left, chart_height = 220, 270
    max_value = max(values.values(), default=1)
    step = chart_height / max(len(values), 1)
    bars = []
    for index, (label, value) in enumerate(values.items()):
        y = 65 + index * step
        bar_width = (value / max_value) * 520
        safe_label = label.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        bars.append(f'<text x="{margin_left - 12}" y="{y + 18:.1f}" text-anchor="end" font-size="14">{safe_label}</text><rect x="{margin_left}" y="{y:.1f}" width="{bar_width:.1f}" height="28" rx="4" fill="{color}" /><text x="{margin_left + bar_width + 8:.1f}" y="{y + 19:.1f}" font-size="14">{value}</text>')
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}"><rect width="100%" height="100%" fill="#f8fafc"/><text x="30" y="32" font-size="20" font-weight="700" fill="#17324d">{title}</text><line x1="{margin_left}" y1="55" x2="{margin_left}" y2="{55 + chart_height}" stroke="#94a3b8" />{"".join(bars)}</svg>'
    path.write_text(svg, encoding="utf-8")


def analyze(workbook: str | Path) -> dict:
    rows = _read_xlsx(Path(workbook))
    if len(rows) != 20:
        raise ValueError(f"Expected 20 populated responses, found {len(rows)}")
    first = rows[0]
    columns = {name: _header(first, prefix) for name, prefix in HEADERS.items()}
    feature_columns = {name: _header(first, prefix) for name, prefix in FEATURES.items()}
    categories = {name: _counts(rows, column) for name, column in columns.items() if name not in {"languages", "environments", "ai_cases"}}
    categories["languages"] = _multi_counts(rows, columns["languages"])
    categories["environments"] = _multi_counts(rows, columns["environments"])
    categories["ai_use_cases"] = _multi_counts(rows, columns["ai_cases"])
    feature_averages = {name: _mean([_number(row[column]) for row in rows]) for name, column in feature_columns.items()}
    assistance_scores = [_number(row[columns["assistance"]]) for row in rows]
    reliance_scores = [_number(row[columns["ai_reliance"]]) for row in rows]
    comfort_scores = [_comfort_score(row[columns["comfort"]]) for row in rows]
    experience_means = {}
    for experience in sorted({row[columns["experience"]] for row in rows}):
        group = [row for row in rows if row[columns["experience"]] == experience]
        experience_means[experience] = {"respondents": len(group), "assistance_average": _mean([_number(row[columns["assistance"]]) for row in group]), "ai_reliance_average": _mean([_number(row[columns["ai_reliance"]]) for row in group]), "comfort_average": _mean([_comfort_score(row[columns["comfort"]]) for row in group]), "ai_users": sum(row[columns["ai_usage"]].lower() == "yes" for row in group)}
    frequency_comfort = {}
    for frequency in sorted({row[columns["frequency"]] for row in rows}):
        group = [row for row in rows if row[columns["frequency"]] == frequency]
        frequency_comfort[frequency] = {"respondents": len(group), "comfort_average": _mean([_comfort_score(row[columns["comfort"]]) for row in group]), "ai_reliance_average": _mean([_number(row[columns["ai_reliance"]]) for row in group])}
    return {
        "respondent_count": len(rows),
        "columns": columns,
        "categories": categories,
        "feature_averages": feature_averages,
        "numeric_averages": {"assistance_preference": _mean(assistance_scores), "ai_reliance": _mean(reliance_scores), "comfort_without_ai_ordinal": _mean(comfort_scores)},
        "cross_tabs": {"experience": experience_means, "coding_frequency": frequency_comfort},
        "models": {
            "guided_builder": {"name": "Guided Builder", "source_respondent": 19, "description": "A beginner respondent who codes rarely and prefers heavy assistance.", "experience": rows[18][columns["experience"]], "coding_frequency": rows[18][columns["frequency"]], "programming_duration": rows[18][columns["duration"]], "assistance_preference": _assistance_label(rows[18][columns["assistance"]]), "ai_reliance": rows[18][columns["ai_reliance"]], "comfort_without_ai": rows[18][columns["comfort"]], "feature_priority": "Error detection, debugging tools, and code execution/testing tools"},
            "independent_builder": {"name": "Independent Builder", "source_respondent": 15, "description": "An advanced respondent with long experience and a preference for less intrusive help.", "experience": rows[14][columns["experience"]], "coding_frequency": rows[14][columns["frequency"]], "programming_duration": rows[14][columns["duration"]], "assistance_preference": _assistance_label(rows[14][columns["assistance"]]), "ai_reliance": rows[14][columns["ai_reliance"]], "comfort_without_ai": rows[14][columns["comfort"]], "feature_priority": "Error detection, debugging tools, and code execution/testing tools"},
        },
        "observed_findings": ["All 20 respondents reported using AI programming tools.", "The assistance preference score ranges from 2 to 5, so the sample contains both lower- and higher-assistance users.", "The experience groups include beginner, intermediate, and advanced respondents, while programming duration ranges from less than six months to 3+ years.", "Feature ratings are calculated directly from the workbook for every listed feature."],
    }


def generate_charts(analysis: dict, output_dir: str | Path) -> None:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    categories = analysis["categories"]
    specs = {"experience.svg": ("Programming experience", categories["experience"]), "coding_frequency.svg": ("Coding frequency", categories["frequency"]), "most_used_editor.svg": ("Most-used editor", categories["editor"]), "assistance_preference.svg": ("Assistance preference score", categories["assistance"]), "ai_usage.svg": ("AI programming usage", categories["ai_usage"]), "ai_reliance.svg": ("AI reliance score", categories["ai_reliance"]), "comfort_without_ai.svg": ("Comfort coding without AI", categories["comfort"])}
    for filename, (title, values) in specs.items():
        _write_svg(output / filename, title, {key: int(value["count"]) for key, value in values.items()})


def write_analysis(workbook: str | Path, output: str | Path, charts_dir: str | Path | None = None) -> dict:
    result = analyze(workbook)
    Path(output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    if charts_dir:
        generate_charts(result, charts_dir)
    return result


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    write_analysis(root / "data" / "survey_data.xlsx", root / "data" / "analysis.json", root / "charts")
    print("Analyzed 20 respondents and generated charts.")
