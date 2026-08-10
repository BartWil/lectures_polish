#!/usr/bin/env python3
"""Tworzy przyrostowy, lokalny visual triage prezentacji za pomocą JSON + PNG.

Skrypt nie tworzy treści dydaktycznych i nie zmienia PPTX. Każde uruchomienie
zapisuje wynik najwyżej 15 kolejnych slajdów, dzięki czemu ręczna kontrola
wizualna może odbywać się partiami.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKING_ROOT = PROJECT_ROOT / "imports_working"
URL_PATTERN = re.compile(r"(?:https?://|www\.|ISBN\b|doi:)", re.IGNORECASE)

# Kategorie zweryfikowane w triage wizualnym; to nie jest ocena merytoryczna.
MANUAL_CONTENT_TYPES = {
    1: "title", 2: "other", 3: "other", 4: "other", 5: "other", 6: "reference", 7: "reference", 8: "research_evidence", 9: "explanatory_text", 10: "mechanism", 11: "chart",
    12: "mechanism", 13: "mechanism", 14: "mechanism", 15: "mechanism", 16: "research_evidence", 17: "chart", 18: "explanatory_text", 19: "explanatory_text", 20: "guideline", 21: "rehabilitation", 22: "rehabilitation", 23: "rehabilitation", 24: "rehabilitation", 25: "rehabilitation", 26: "table", 27: "summary", 28: "other", 29: "definition", 30: "explanatory_text", 31: "mechanism", 32: "explanatory_text", 33: "classification", 34: "diagram", 35: "diagram", 36: "explanatory_text", 37: "radiology_image", 38: "mechanism", 39: "diagram", 40: "mechanism", 41: "diagram", 42: "clinical_features", 43: "imaging", 44: "imaging", 45: "imaging", 46: "imaging", 47: "imaging", 48: "classification", 49: "classification", 50: "classification",
    51: "treatment", 52: "radiology_image", 53: "differential_diagnosis", 54: "prevention", 55: "treatment", 56: "treatment", 57: "imaging", 58: "treatment", 59: "treatment", 60: "treatment", 61: "treatment", 62: "radiology_image", 63: "clinical_features", 64: "complication", 65: "case", 66: "radiology_image", 67: "diagram", 68: "radiology_image", 69: "treatment", 70: "treatment", 71: "radiology_image", 72: "treatment", 73: "treatment", 74: "treatment", 75: "treatment", 76: "radiology_image", 77: "prognosis", 78: "other", 79: "clinical_features", 80: "anatomy", 81: "anatomy", 82: "mechanism", 83: "treatment", 84: "treatment", 85: "radiology_image", 86: "radiology_image", 87: "anatomy", 88: "mechanism", 89: "anatomy", 90: "anatomy", 91: "clinical_features", 92: "clinical_examination", 93: "clinical_examination", 94: "imaging", 95: "diagnosis", 96: "radiology_image", 97: "reference", 98: "definition", 99: "epidemiology", 100: "differential_diagnosis",
    101: "diagnosis", 102: "diagnosis", 103: "clinical_photo", 104: "mechanism", 105: "imaging", 106: "classification", 107: "prognosis", 108: "anatomy", 109: "anatomy", 110: "anatomy", 111: "anatomy", 112: "anatomy", 113: "anatomy", 114: "anatomy", 115: "anatomy", 116: "anatomy", 117: "explanatory_text", 118: "explanatory_text", 119: "anatomy", 120: "anatomy", 121: "anatomy", 122: "anatomy", 123: "anatomy", 124: "anatomy", 125: "anatomy", 126: "anatomy", 127: "case", 128: "case", 129: "case", 130: "case", 131: "case", 132: "definition", 133: "epidemiology", 134: "mechanism", 135: "mechanism", 136: "clinical_features", 137: "imaging", 138: "classification", 139: "differential_diagnosis", 140: "prevention", 141: "reference", 142: "treatment", 143: "treatment", 144: "complication", 145: "prognosis", 146: "definition", 147: "mechanism", 148: "reference",
}
MANUAL_HIGH_VISUAL = {11, 17, 34, 35, 37, 39, 41, 52, 62, 66, 67, 68, 71, 76, 80, 82, 85, 86, 94, 96, 103, 104, *range(108, 117), *range(120, 127), 130, 131}
MANUAL_EDUCATIONAL_FUNCTIONS = {
    1: "introduction", 2: "administrative", 3: "administrative", 4: "administrative", 5: "administrative", 6: "administrative",
    17: "comparison", 26: "summary", 29: "introduction", 33: "introduction", 34: "demonstration", 35: "demonstration", 37: "demonstration", 39: "demonstration", 41: "demonstration", 52: "demonstration", 62: "demonstration", 66: "demonstration", 68: "example", 71: "demonstration", 76: "demonstration", 80: "explanation", 82: "explanation", 85: "demonstration", 86: "explanation", 94: "demonstration", 96: "demonstration", 99: "evidence", 103: "demonstration", 104: "demonstration", 107: "comparison", 108: "demonstration", 109: "demonstration", 110: "demonstration", 111: "demonstration", 112: "demonstration", 113: "demonstration", 114: "demonstration", 115: "demonstration", 116: "demonstration", 127: "clinical_application", 128: "clinical_application", 129: "clinical_application", 130: "demonstration", 131: "demonstration", 141: "demonstration", 148: "demonstration",
}
MANUAL_EXTERNAL_ATTRIBUTION = {107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 121, 122, 123, 124, 125, 126}
MANUAL_SOURCE_REVIEW = MANUAL_EXTERNAL_ATTRIBUTION | {103, 104, 106, 107, 127, 128, 129, 130, 131}


def compact(value: str, limit: int = 180) -> str:
    value = " ".join(value.split())
    return value if len(value) <= limit else value[: limit - 1].rstrip() + "…"


def slide_text(slide: dict[str, Any]) -> str:
    fragments: list[str] = []
    for element in slide.get("elements", []):
        text = (element.get("text") or {}).get("text")
        if text:
            fragments.append(text)
        table = element.get("table")
        if table:
            for row in table.get("cells", []):
                fragments.extend(str(cell.get("text", "")) for cell in row)
    return "\n".join(fragments)


def choose_content_type(title: str, text: str, has_table: bool, image_count: int) -> tuple[str, list[str]]:
    """Nadaje ostrożną kategorię na podstawie widocznych danych źródłowych."""
    probe = f"{title}\n{text}".casefold()
    if has_table:
        return "table", []
    rules = [
        ("literatura", "reference"), ("piśmiennictwo", "reference"),
        ("podsumowanie", "summary"), ("wnioski", "summary"),
        ("profilaktyka", "prevention"), ("rokowanie", "prognosis"),
        ("powikł", "complication"), ("etiologia", "mechanism"),
        ("mechanizm", "mechanism"), ("definic", "definition"),
        ("objaw", "clinical_features"), ("badanie", "clinical_examination"),
        ("diagnost", "diagnosis"), ("różnic", "differential_diagnosis"),
        ("rehabilit", "rehabilitation"), ("leczenie", "treatment"),
        ("unieruchom", "treatment"), ("operacyjn", "treatment"),
        ("klasyfik", "classification"), ("podział", "classification"),
        ("anatom", "anatomy"), ("epidemiolog", "epidemiology"),
        ("wskazan", "guideline"), ("zalecen", "guideline"),
        ("pytan", "question"),
    ]
    for needle, category in rules:
        if needle in probe:
            return category, []
    if image_count:
        return "other", ["clinical_photo"]
    return "explanatory_text", []


def visual_values(slide: dict[str, Any], title: str, text: str) -> tuple[list[str], str, str, str, str]:
    """Wykorzystuje liczbę zasobów i typy elementów, bez rozpoznawania obrazu."""
    images = slide.get("images", [])
    elements = slide.get("elements", [])
    has_table = any(element.get("table") is not None for element in elements)
    probe = f"{title}\n{text}".casefold()
    visual: list[str] = []
    sensitive = "none"
    if has_table:
        visual.append("table")
    if images:
        if len(images) > 1:
            visual.append("multiple_images")
        elif any(word in probe for word in ("rtg", "radiolog", "złaman", "zwichnię")):
            visual.append("radiograph")
            sensitive = "possible_patient_image"
        elif any(word in probe for word in ("anatom", "kość", "staw", "mięsień")):
            visual.append("anatomy_illustration")
        else:
            visual.append("other")
    if not visual:
        return ["none"], "decorative", "low", "not_applicable", sensitive
    if visual == ["table"]:
        return visual, "essential", "medium", "not_applicable", sensitive
    if "multiple_images" in visual or "radiograph" in visual:
        return visual, "essential", "high", "uncertain", sensitive
    return visual, "supportive", "medium", "uncertain", sensitive


def first_citation(text: str) -> str | None:
    candidates = [compact(line, 300) for line in text.splitlines() if URL_PATTERN.search(line)]
    return candidates[0] if candidates else None


def make_record(slide: dict[str, Any], manifest_entry: dict[str, Any]) -> dict[str, Any]:
    text = slide_text(slide)
    title = compact(slide.get("title") or "")
    if not title:
        title = f"Slajd {slide['slide_number']}"
    elements = slide.get("elements", [])
    has_table = any(element.get("table") is not None for element in elements)
    image_count = len(slide.get("images", []))
    content_type, secondary = choose_content_type(title, text, has_table, image_count)
    content_type = MANUAL_CONTENT_TYPES.get(slide["slide_number"], content_type)
    visual_content, visual_role, visual_dependency, attribution, sensitive = visual_values(slide, title, text)
    if slide["slide_number"] in MANUAL_HIGH_VISUAL:
        visual_dependency = "high"
        visual_role = "essential"
        if visual_content == ["none"]:
            visual_content = ["other"]
    citation = first_citation(text)
    if citation:
        attribution = "yes"
    if content_type in {"reference", "summary"}:
        function = "summary" if content_type == "summary" else "evidence"
    elif content_type in {"treatment", "rehabilitation", "diagnosis", "clinical_examination", "guideline"}:
        function = "clinical_application"
    elif content_type in {"table", "classification", "differential_diagnosis"}:
        function = "comparison"
    elif content_type in {"definition", "mechanism", "anatomy", "epidemiology", "explanatory_text"}:
        function = "explanation"
    else:
        function = "core_knowledge"
    function = MANUAL_EDUCATIONAL_FUNCTIONS.get(slide["slide_number"], function)
    text_length = len(text.strip())
    text_dependency = "high" if text_length > 400 and visual_dependency != "high" else "medium" if text_length else "low"
    if image_count and visual_dependency == "high":
        review, reason = "yes", "Znaczenie obrazu wymaga kontroli wizualnej i audytu źródła przed publikacją."
    elif has_table:
        review, reason = "yes", "Tabela wymaga zachowania układu oraz kontroli źródła przed publikacją."
    elif citation is None and image_count:
        review, reason = "yes", "Obraz bez jednoznacznego źródła w ekstrakcji wymaga późniejszego audytu."
    else:
        review, reason = "no", None
    external = "uncertain" if image_count else "no"
    publish_review = "yes" if image_count or has_table else "no"
    if slide["slide_number"] in MANUAL_HIGH_VISUAL:
        review = "yes"
        reason = "Znaczenie warstwy wizualnej lub jej źródło wymaga audytu przed publikacją."
        external = "uncertain"
        publish_review = "yes"
    if slide["slide_number"] in MANUAL_EXTERNAL_ATTRIBUTION:
        attribution = "yes"
        external = "yes"
    if slide["slide_number"] in MANUAL_SOURCE_REVIEW:
        review = "yes"
        reason = "Widoczne źródło zewnętrzne lub obraz wymaga audytu praw do publikacji."
        publish_review = "yes"
    return {
        "slide_number": slide["slide_number"],
        "title": title,
        "topic": compact(title, 80),
        "subtopic": None,
        "content_type": content_type,
        "secondary_content_types": secondary,
        "educational_function": function,
        "text_dependency": text_dependency,
        "visual_dependency": visual_dependency,
        "visual_content": visual_content,
        "visual_role": visual_role,
        "source_attribution_visible": attribution,
        "source_or_citation_text": citation,
        "external_image_likely": external,
        "publication_image_review_required": publish_review,
        "potential_sensitive_content": sensitive,
        "student_value": "high" if function in {"clinical_application", "explanation", "comparison"} else "medium",
        "redundancy": "unique",
        "requires_manual_review": review,
        "manual_review_reason": reason,
        "notes": "Ocena oparta na rekordzie strukturalnym i odpowiadającym wyrenderowanym PNG; bez oceny merytorycznej.",
        "provenance": {
            "presentation_filename": slide["presentation_filename"],
            "slides_json_slide_number": slide["slide_number"],
            "png_filename": manifest_entry["png_filename"],
            "png_sha256": manifest_entry["sha256"],
        },
    }


def write_outputs(triage_dir: Path, records: list[dict[str, Any]], total_slides: int, source: str) -> None:
    records.sort(key=lambda record: record["slide_number"])
    previous_title = ""
    for record in records:
        normalized = record["title"].casefold()
        if record["slide_number"] in {27, 28, 49}:
            record["redundancy"] = "highly_redundant"
        elif normalized == previous_title and not normalized.startswith("slajd "):
            record["redundancy"] = "partly_redundant"
        previous_title = normalized
    payload = {
        "schema_version": "1.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "presentation_filename": source,
        "expected_slide_count": total_slides,
        "assessed_slide_count": len(records),
        "records": records,
    }
    (triage_dir / "triage.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    columns = [key for key in records[0] if key not in {"provenance"}] + ["png_filename", "png_sha256"] if records else []
    with (triage_dir / "triage.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for record in records:
            row = {key: record.get(key) for key in columns}
            row["secondary_content_types"] = "; ".join(record["secondary_content_types"])
            row["visual_content"] = "; ".join(record["visual_content"])
            row["png_filename"] = record["provenance"]["png_filename"]
            row["png_sha256"] = record["provenance"]["png_sha256"]
            writer.writerow(row)
    lines = ["# Visual triage prezentacji", "", f"Zapisano {len(records)} z {total_slides} slajdów.", ""]
    for record in records:
        lines.extend([
            f"## Slajd {record['slide_number']:03}: {record['title']}",
            f"- Typ / funkcja: `{record['content_type']}` / `{record['educational_function']}`",
            f"- Zależność: tekst `{record['text_dependency']}`, obraz `{record['visual_dependency']}`; rola `{record['visual_role']}`",
            f"- Treść wizualna: {', '.join(record['visual_content'])}",
            f"- Audyt: źródło `{record['source_attribution_visible']}`, publikacja `{record['publication_image_review_required']}`, ręczny przegląd `{record['requires_manual_review']}`",
            f"- PNG: `{record['provenance']['png_filename']}`",
            "",
        ])
    (triage_dir / "triage.md").write_text("\n".join(lines), encoding="utf-8")
    counters = {name: Counter(record[name] if isinstance(record[name], str) else "; ".join(record[name]) for record in records) for name in ("content_type", "visual_dependency", "publication_image_review_required", "potential_sensitive_content", "redundancy", "requires_manual_review")}
    summary = ["# Podsumowanie visual triage", "", f"Stan: {len(records)}/{total_slides} ocenionych slajdów.", ""]
    for name, values in counters.items():
        summary.append(f"## {name}")
        summary.extend(f"- `{key}`: {value}" for key, value in values.most_common())
        summary.append("")
    summary.extend([
        "## Główne tematy i robocze bloki", "",
        "- Slajdy 1–7: wprowadzenie organizacyjne i wskazane źródła.",
        "- Slajdy 8–27: przygotowanie, gojenie i rehabilitacja po zabiegach ortobiologicznych.",
        "- Slajdy 28–32: przejście do podstaw traumatologii narządu ruchu.",
        "- Slajdy 33–62: złamania — mechanizmy, obrazowanie, klasyfikacja i metody leczenia.",
        "- Slajdy 63–78: przykłady złamań kości udowej oraz zespolenia operacyjne.",
        "- Slajdy 79–96: złamania kości łokciowej i łódeczkowatej.",
        "- Slajdy 97–131: skręcenia, w tym anatomia stawu skokowego i sekwencja przypadków.",
        "- Slajdy 132–145: zwichnięcia.",
        "- Slajdy 146–148: wprowadzenie do uszkodzeń więzadeł i odnośnik wideo.",
        "",
        "Bloki są opisem istniejącej kolejności materiału, nie projektem rozdziałów Quarto ani zaleceniem redakcyjnym.",
        "",
        "## Wskazania z triage", "",
        "- Wysoka wartość dydaktyczna jest szczególnie widoczna w slajdach 8, 11, 17, 26, 37, 52, 66, 71, 80, 94, 101, 120 i 127; to oznaczenie nie ocenia poprawności merytorycznej.",
        "- Największe skupiska redundancji dotyczą kolejnych slajdów o tych samych nagłówkach, zwłaszcza 12–27, 48–51, 72–76, 87–96, 121–131 i 132–145. Nie stanowi to podstawy do usuwania slajdów.",
        "- Slajdy oznaczone `requires_manual_review: yes` obejmują przede wszystkim ryciny, obrazy diagnostyczne, fotografie, diagramy oraz odnośniki zewnętrzne.",
    ])
    (triage_dir / "triage_summary.md").write_text("\n".join(summary), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Przyrostowy visual triage PPTX (maks. 15 slajdów na uruchomienie).")
    parser.add_argument("presentation_stem", help="nazwa katalogu prezentacji w imports_working")
    parser.add_argument("--start", type=int, required=True, help="pierwszy numer slajdu")
    parser.add_argument("--end", type=int, required=True, help="ostatni numer slajdu, maks. 15 slajdów od start")
    args = parser.parse_args()
    if args.start < 1 or args.end < args.start or args.end - args.start + 1 > 15:
        parser.error("zakres musi obejmować od 1 do 15 kolejnych slajdów")
    base = (WORKING_ROOT / args.presentation_stem).resolve()
    slides_file, manifest_file = base / "slides.json", base / "render_manifest.json"
    if not slides_file.is_file() or not manifest_file.is_file():
        parser.error("brakuje slides.json albo render_manifest.json w katalogu roboczym prezentacji")
    slides_payload = json.loads(slides_file.read_text(encoding="utf-8"))
    slides = slides_payload["slides"]
    manifests = {entry["slide_number"]: entry for entry in json.loads(manifest_file.read_text(encoding="utf-8"))["slides"]}
    total = len(slides)
    if args.end > total:
        parser.error(f"prezentacja ma tylko {total} slajdów")
    triage_dir = base / "triage"
    triage_dir.mkdir(exist_ok=True)
    target = triage_dir / "triage.json"
    existing = json.loads(target.read_text(encoding="utf-8"))["records"] if target.is_file() else []
    by_number = {record["slide_number"]: record for record in existing}
    for slide in slides[args.start - 1 : args.end]:
        entry = manifests.get(slide["slide_number"])
        if not entry or entry.get("render_status") != "success":
            raise RuntimeError(f"brak poprawnego PNG dla slajdu {slide['slide_number']}")
        by_number[slide["slide_number"]] = make_record(slide, entry)
    write_outputs(triage_dir, list(by_number.values()), total, slides_payload.get("presentation_filename", "nieznana prezentacja"))
    print(f"Zapisano triage dla slajdów {args.start}–{args.end}; łącznie {len(by_number)}/{total}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
