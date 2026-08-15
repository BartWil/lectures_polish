#!/usr/bin/env python3
"""Ekstrahuje strukturę protokołu rehabilitacyjnego z tekstowego PDF.

Skrypt nie wykonuje OCR, nie ocenia zaleceń i nie tworzy materiału dla
studentów. Wyniki są roboczym odwzorowaniem: dokument → strona → sekcja →
element. Rozpoznawanie faz i kategorii ma charakter mechaniczny; każdy rekord
z inventory działań wymaga późniejszego audytu dowodów.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

import pdfplumber


SCHEMA_VERSION = "1.0"
LINE_TOLERANCE = 2.5
BULLET_RE = re.compile(r"^(?:[•●◦▪‣*]|[-–—]|o)\s+(?P<text>.+)$")
PHASE_RE = re.compile(r"^phase\s+(?P<label>[ivxlcdm]+|\d+)\s*:\s*(?P<name>.*)$", re.I)
TIME_RE = re.compile(
    r"\b(?:\d+(?:\s*[-–]\s*\d+)?\s*(?:day|days|week|weeks|month|months)|"
    r"\d+\+\s*(?:week|weeks|month|months)|post[- ]?op)\b",
    re.I,
)
THRESHOLD_RE = re.compile(r"(?:≥|≤|>|<|\bwithin\b|\bequal to\b|\bno more than\b)\s*[^.;]{0,80}", re.I)
CONDITIONAL_RE = re.compile(
    r"\b(?:if|unless|once|when|as long as|only|per\s+(?:md|physician|surgeon)|"
    r"depending on|based on|with|without)\b",
    re.I,
)
NORMATIVE_RE = re.compile(
    r"\b(?:should|may|must|do not|avoid|continue|begin|start|progress|"
    r"discontinue|follow|consult|keep|protect|restore|maintain|return)\b",
    re.I,
)


@dataclass
class TextLine:
    page: int
    reading_order: int
    text: str
    x0: float
    top: float
    x1: float
    bottom: float
    size: float | None
    fontname: str | None


def normalise(text: str) -> str:
    """Usuwa wyłącznie łamanie wiersza i nadmiarowe białe znaki."""
    return re.sub(r"\s+", " ", text).strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_dump(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def group_words_into_lines(page: Any, page_number: int) -> list[TextLine]:
    words = page.extract_words(extra_attrs=["fontname", "size"], keep_blank_chars=False)
    words.sort(key=lambda item: (round(float(item["top"]), 1), float(item["x0"])))
    grouped: list[list[dict[str, Any]]] = []

    for word in words:
        if not grouped or abs(float(word["top"]) - float(grouped[-1][0]["top"])) > LINE_TOLERANCE:
            grouped.append([word])
        else:
            grouped[-1].append(word)

    result: list[TextLine] = []
    for index, group in enumerate(grouped, start=1):
        group.sort(key=lambda item: float(item["x0"]))
        result.append(
            TextLine(
                page=page_number,
                reading_order=index,
                text=normalise(" ".join(str(item["text"]) for item in group)),
                x0=round(min(float(item["x0"]) for item in group), 2),
                top=round(min(float(item["top"]) for item in group), 2),
                x1=round(max(float(item["x1"]) for item in group), 2),
                bottom=round(max(float(item["bottom"]) for item in group), 2),
                size=round(max(float(item.get("size") or 0) for item in group), 2) or None,
                fontname=next((str(item.get("fontname")) for item in group if item.get("fontname")), None),
            )
        )
    return result


def heading_kind(text: str) -> str | None:
    """Klasyfikuje wyłącznie widoczne etykiety dokumentu, bez oceny treści."""
    value = normalise(text).rstrip(":").casefold()
    if PHASE_RE.match(value):
        return "phase"
    if value in {"references", "reference"}:
        return "references"
    if value == "return to running program":
        return "subprogram_running"
    if value == "agility and plyometric program":
        return "subprogram_agility_plyometrics"
    if value in {"general considerations", "general consideration"}:
        return "general_considerations"
    if value.startswith("considerations with concomitant"):
        return "concomitant_procedure_modifications"
    if value.startswith("considerations for allograft") or value.startswith("graft-specific"):
        return "graft_specific_modifications"
    if value in {"precautions", "post-operative considerations", "postoperative considerations"}:
        return "precautions"
    if value in {"weight bearing walking", "weight-bearing walking", "weight bearing", "weight-bearing"}:
        return "weight_bearing"
    if value in {"range of motion/mobility", "range of motion", "mobility"}:
        return "ROM_mobility"
    if value == "strengthening":
        return "strengthening"
    if value in {"balance/proprioception", "balance and proprioception", "neuromuscular training"}:
        return "balance_neuromuscular"
    if value in {"cardio", "cardiovascular activity"}:
        return "cardiovascular_activity"
    if value == "plyometrics":
        return "plyometrics"
    if value in {"agility", "sport-specific training", "sport specific training"}:
        return "sport_specific_training"
    if value == "criteria to progress":
        return "criteria_to_progress"
    if value in {"return to sport", "return to run"}:
        return "return_to_sport"
    if value == "functional assessment":
        return "objective_measures"
    if value in {"koos-sports questionnaire", "international knee documentation committee subjective knee evaluation", "acl-rsi"}:
        return "patient_reported_outcomes"
    if value in {"recommendations", "recommendation"}:
        return "recommendations"
    if value in {"goals", "rehabilitation goals"}:
        return "goals"
    if value in {"interventions", "additional interventions"}:
        return "interventions"
    if value in {"red flags", "when to call your doctor"}:
        return "red_flags"
    return None


def split_leading_section_label(text: str) -> tuple[str | None, str]:
    """Rozdziela etykietę lewej komórki tabeli od pierwszego punktu z prawej.

    W wielu protokołach PDF oba pola mają identyczną współrzędną pionową,
    dlatego ekstrakcja kolejności czytania łączy je w jeden wiersz.
    """
    labels = [
        "Rehabilitation Goals", "Additional Interventions", "Criteria to Progress",
        "Weight Bearing Walking", "Range of motion/Mobility", "Balance/proprioception",
        "Patient Education", "Functional Assessment", "Strengthening", "Plyometrics",
        "Agility", "Cardio", "Recommendations", "Rehabilitation", "Criteria to", "Progress",
        "Goals", "Interventions",
    ]
    for label in labels:
        pattern = re.compile(rf"^{re.escape(label)}\s+(?=(?:[•●◦▪‣*]|[-–—]|o)\s+)", re.I)
        match = pattern.match(text)
        if match:
            return label, text[match.end():]
    return None, text


def is_heading(line: TextLine) -> bool:
    kind = heading_kind(line.text)
    if kind is not None:
        return True
    letters = re.sub(r"[^A-Za-z]", "", line.text)
    return bool(letters) and letters.isupper() and len(line.text) < 100 and line.size is not None and line.size >= 9


def action_type(section_kind: str | None, text: str) -> str:
    lowered = text.casefold()
    if any(term in lowered for term in ("koos", "international knee documentation", "acl-rsi", "patient-reported")):
        return "patient_reported_outcomes"
    if section_kind in {
        "weight_bearing", "ROM_mobility", "strengthening", "balance_neuromuscular",
        "cardiovascular_activity", "plyometrics", "sport_specific_training", "precautions",
        "criteria_to_progress", "patient_reported_outcomes", "graft_specific_modifications",
        "concomitant_procedure_modifications", "red_flags", "goals", "interventions",
        "recommendations", "objective_measures",
    }:
        return section_kind
    if "brace" in lowered:
        return "brace"
    if "weight bearing" in lowered or "weight-bearing" in lowered:
        return "weight_bearing"
    if "range of motion" in lowered or " rom " in f" {lowered} ":
        return "ROM"
    if "hop" in lowered:
        return "hop_threshold"
    if "run" in lowered or "jog" in lowered:
        return "running"
    if "return to sport" in lowered or "full play" in lowered:
        return "RTS_criterion"
    if "clearance" in lowered or "physician" in lowered or "surgeon" in lowered:
        return "physician_clearance"
    if "allograft" in lowered or "autograft" in lowered or "graft" in lowered:
        return "graft_specific_precaution"
    return "other"


def action_tags(text: str) -> list[str]:
    lowered = text.casefold()
    tags: list[str] = []
    if any(term in lowered for term in ("hhd", "isokinetic", "hop testing", "modified stroke test", "joint position sense")):
        tags.append("objective_measure")
    if any(term in lowered for term in ("koos", "international knee documentation", "acl-rsi", "questionnaire")):
        tags.append("PROM")
    if any(term in lowered for term in ("allograft", "autograft", "graft donor")):
        tags.append("graft_specific")
    if "meniscus repair" in lowered or "concomitant" in lowered:
        tags.append("concomitant_procedure")
    return tags


def phase_name_and_time(text: str) -> tuple[str, str | None]:
    match = PHASE_RE.match(text)
    if not match:
        return text, None
    name = normalise(match.group("name"))
    time_matches = TIME_RE.findall(name)
    specific = [match for match in time_matches if match.casefold() not in {"post-op", "post op"}]
    return text, max(specific or time_matches, key=len, default=None)


def make_element_id(page: int, element_type: str, ordinal: int) -> str:
    return f"p{page:03d}-{element_type}-{ordinal:03d}"


def serialise_line(line: TextLine, ordinal: int) -> dict[str, Any]:
    kind = heading_kind(line.text)
    # Nazwy podprogramów mogą występować jako wewnętrzne odnośniki w fazie.
    # Tylko większy tekst traktujemy jako nagłówek rozpoczynający podprogram;
    # mniejszy zapis zachowujemy jako link strukturalny bez tworzenia akcji.
    if kind in {"subprogram_running", "subprogram_agility_plyometrics"} and (line.size or 0) < 14:
        kind = f"{kind}_link"
    return {
        "element_id": make_element_id(line.page, "text", ordinal),
        "type": "text_block",
        "text": line.text,
        "reading_order": line.reading_order,
        "bbox": {"x0": line.x0, "top": line.top, "x1": line.x1, "bottom": line.bottom},
        "metadata": {"font_size": line.size, "font_name": line.fontname},
        "heading_kind": kind,
    }


def extract_tables(page: Any, page_number: int) -> list[dict[str, Any]]:
    tables: list[dict[str, Any]] = []
    for ordinal, table in enumerate(page.find_tables(), start=1):
        rows = [[normalise(cell or "") for cell in row] for row in table.extract()]
        tables.append(
            {
                "element_id": make_element_id(page_number, "table", ordinal),
                "type": "table",
                "bbox": {
                    "x0": round(float(table.bbox[0]), 2), "top": round(float(table.bbox[1]), 2),
                    "x1": round(float(table.bbox[2]), 2), "bottom": round(float(table.bbox[3]), 2),
                },
                "rows": rows,
                "metadata": {"row_count": len(rows), "column_count": max((len(row) for row in rows), default=0)},
            }
        )
    return tables


def extract_hyperlinks(page: Any, page_number: int) -> list[dict[str, Any]]:
    links: list[dict[str, Any]] = []
    for ordinal, link in enumerate(page.hyperlinks, start=1):
        links.append(
            {
                "element_id": make_element_id(page_number, "link", ordinal),
                "type": "hyperlink",
                "uri": link.get("uri"),
                "bbox": {key: round(float(link[key]), 2) for key in ("x0", "top", "x1", "bottom") if key in link},
                "metadata": {"annotated_text": link.get("title")},
            }
        )
    return links


def add_action(
    actions: list[dict[str, Any]],
    *, source_id: str,
    page: int,
    phase_id: str | None,
    section_name: str | None,
    section_kind: str | None,
    text: str,
    source_element_id: str,
    source_order: int,
    source_type: str,
    category_override: str | None = None,
) -> None:
    value = normalise(text)
    if not value or len(value) < 3:
        return
    action_number = len(actions) + 1
    actions.append(
        {
            "action_id": f"{source_id.upper()}-{action_number:03d}",
            "phase": phase_id,
            "page": page,
            "category": category_override or action_type(section_kind, value),
            "original_context": section_name,
            "normalized_action": value,
            "timing_or_timeframe": TIME_RE.findall(value),
            "criterion_or_threshold": THRESHOLD_RE.findall(value),
            "measurement_method": (
                "HHD_or_isokinetic" if re.search(r"\b(?:HHD|isokinetic)\b", value, re.I) else None
            ),
            "tags": action_tags(value),
            "graft_or_procedure_modifier": bool(re.search(r"\b(?:allograft|autograft|graft|meniscus repair)\b", value, re.I)),
            "conditionality": bool(CONDITIONAL_RE.search(value)),
            "source_page": page,
            "source_element_id": source_element_id,
            "source_order": source_order,
            "source_type": source_type,
            "future_evidence_audit_required": "yes",
        }
    )


def collect_actions(
    pages: list[dict[str, Any]], source_id: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    actions: list[dict[str, Any]] = []
    phases: list[dict[str, Any]] = []
    active_phase: dict[str, Any] | None = None
    active_subprogram: str | None = None
    active_section_name: str | None = None
    active_section_kind: str | None = None
    pending_bullet: dict[str, Any] | None = None

    def flush_bullet() -> None:
        nonlocal pending_bullet
        if pending_bullet is not None:
            payload = dict(pending_bullet)
            payload.pop("bullet_x0", None)
            add_action(actions, source_id=source_id, **payload)
            pending_bullet = None

    for page in pages:
        for element in page["text_blocks"]:
            line = TextLine(
                page=page["page_number"], reading_order=element["reading_order"], text=element["text"],
                x0=element["bbox"]["x0"], top=element["bbox"]["top"], x1=element["bbox"]["x1"],
                bottom=element["bbox"]["bottom"], size=element["metadata"]["font_size"],
                fontname=element["metadata"]["font_name"],
            )
            kind = element["heading_kind"]
            phase_match = PHASE_RE.match(line.text)
            if phase_match:
                flush_bullet()
                phase_name, timeframe = phase_name_and_time(line.text)
                active_phase = {
                    "phase_id": f"{source_id.upper()}-PHASE-{len(phases) + 1:02d}",
                    "original_phase_name": phase_name,
                    "program": active_subprogram or "main_protocol",
                    "page_numbers": [line.page],
                    "stated_time_window": timeframe,
                    "goals": [], "precautions": [], "interventions": [], "criteria_to_progress": [],
                    "objective_measures": [], "PROMs": [], "graft_specific_notes": [],
                    "concomitant_injury_notes": [], "links_to_subprograms": [], "source_pages": [line.page],
                }
                phases.append(active_phase)
                active_section_name, active_section_kind = line.text, "phase"
                continue
            if kind in {"subprogram_running", "subprogram_agility_plyometrics"}:
                flush_bullet()
                active_phase = None
                active_subprogram = kind.removeprefix("subprogram_")
                active_section_name, active_section_kind = line.text, kind
                continue
            if kind in {"subprogram_running_link", "subprogram_agility_plyometrics_link"}:
                flush_bullet()
                if active_phase is not None:
                    active_phase["links_to_subprograms"].append(
                        {
                            "subprogram": kind.removeprefix("subprogram_").removesuffix("_link"),
                            "label": line.text,
                            "source_page": line.page,
                            "source_element_id": element["element_id"],
                            "source_order": line.reading_order,
                        }
                    )
                continue
            if kind is not None:
                flush_bullet()
                if kind == "references":
                    active_phase = None
                active_section_name, active_section_kind = line.text, kind
                continue

            # W źródłowym układzie PDF nazwy podprogramów w fazie V są
            # sklejone z etykietą tabeli i punktem listy. Zapisujemy je jako
            # linki strukturalne, bez przekształcania ich w nowe akcje.
            inline_subprograms = (
                ("running", "Return to Running Program"),
                ("agility_plyometrics", "Agility and Plyometric Program"),
            )
            matched_subprogram = next(
                ((identifier, label) for identifier, label in inline_subprograms if label.casefold() in line.text.casefold()),
                None,
            )
            if matched_subprogram is not None and active_phase is not None:
                identifier, label = matched_subprogram
                active_phase["links_to_subprograms"].append(
                    {
                        "subprogram": identifier,
                        "label": label,
                        "source_page": line.page,
                        "source_element_id": element["element_id"],
                        "source_order": line.reading_order,
                    }
                )
                if line.text.casefold().startswith("interventions "):
                    active_section_name, active_section_kind = "Interventions", "interventions"
                continue

            if line.text.casefold().startswith("interventions "):
                flush_bullet()
                if active_section_kind == "ROM_mobility":
                    line = TextLine(
                        page=line.page, reading_order=line.reading_order,
                        text=line.text[len("Interventions "):], x0=line.x0, top=line.top,
                        x1=line.x1, bottom=line.bottom, size=line.size, fontname=line.fontname,
                    )
                else:
                    active_section_name, active_section_kind = "Interventions", "interventions"
                    continue
            if "range of motion/mobility" in line.text.casefold() and not BULLET_RE.match(line.text):
                flush_bullet()
                active_section_name, active_section_kind = "Range of motion/Mobility", "ROM_mobility"
                continue

            section_label, remaining_text = split_leading_section_label(line.text)
            if section_label is not None:
                flush_bullet()
                active_section_name = section_label
                active_section_kind = {
                    "rehabilitation": "goals",
                    "criteria to": "criteria_to_progress",
                    "progress": "criteria_to_progress",
                }.get(section_label.casefold(), heading_kind(section_label))
                line = TextLine(
                    page=line.page, reading_order=line.reading_order, text=remaining_text,
                    x0=line.x0, top=line.top, x1=line.x1, bottom=line.bottom,
                    size=line.size, fontname=line.fontname,
                )

            bullet = BULLET_RE.match(line.text)
            if bullet:
                flush_bullet()
                pending_bullet = {
                    "page": line.page,
                    "phase_id": active_phase["phase_id"] if active_phase else None,
                    "section_name": active_section_name,
                    "section_kind": active_section_kind,
                    "text": bullet.group("text"),
                    "source_element_id": element["element_id"],
                    "source_order": line.reading_order,
                    "source_type": "bullet_text",
                    "bullet_x0": line.x0,
                }
                continue

            if pending_bullet and line.x0 >= float(pending_bullet["bullet_x0"]) + 3 and not is_heading(line):
                pending_bullet["text"] = f"{pending_bullet['text']} {line.text}"
                continue
            flush_bullet()

            if NORMATIVE_RE.search(line.text):
                add_action(
                    actions, source_id=source_id, page=line.page,
                    phase_id=active_phase["phase_id"] if active_phase else None,
                    section_name=active_section_name, section_kind=active_section_kind,
                    text=line.text, source_element_id=element["element_id"],
                    source_order=line.reading_order, source_type="normative_text",
                )

        flush_bullet()

        for table in page["tables"]:
            # Dwukolumnowe tabele opisowe są już odwzorowane przez tekst i punkty.
            # Szersze tabele są zwykle harmonogramami; zachowujemy każdy wiersz jako
            # jedną nieinterpretowaną akcję, aby nie gubić relacji dzień–dawka.
            if table["metadata"]["column_count"] < 3:
                continue
            for row_index, row in enumerate(table["rows"], start=1):
                values = [cell for cell in row if cell]
                if len(values) < 2:
                    continue
                add_action(
                    actions, source_id=source_id, page=page["page_number"],
                    phase_id=active_phase["phase_id"] if active_phase else None,
                    section_name=active_section_name, section_kind=active_section_kind,
                    text=" | ".join(values), source_element_id=table["element_id"],
                    source_order=10000 + row_index, source_type="table_row",
                    category_override="table_schedule",
                )

    phase_by_id = {phase["phase_id"]: phase for phase in phases}
    for action in actions:
        phase = phase_by_id.get(action["phase"])
        if phase is None:
            continue
        phase["page_numbers"].append(action["source_page"])
        phase["source_pages"].append(action["source_page"])
        field = {
            "goals": "goals", "precautions": "precautions", "interventions": "interventions",
            "criteria_to_progress": "criteria_to_progress", "objective_measures": "objective_measures",
            "patient_reported_outcomes": "PROMs", "graft_specific_modifications": "graft_specific_notes",
            "concomitant_procedure_modifications": "concomitant_injury_notes",
        }.get(action["category"])
        if field:
            phase[field].append(action["action_id"])
        if action["category"] in {
            "weight_bearing", "brace", "ROM", "ROM_mobility", "strengthening",
            "balance_neuromuscular", "cardiovascular_activity", "plyometrics",
            "sport_specific_training", "running", "recommendations", "table_schedule",
        }:
            phase["interventions"].append(action["action_id"])
        if "objective_measure" in action["tags"]:
            phase["objective_measures"].append(action["action_id"])
        if "PROM" in action["tags"]:
            phase["PROMs"].append(action["action_id"])
        if "graft_specific" in action["tags"]:
            phase["graft_specific_notes"].append(action["action_id"])
        if "concomitant_procedure" in action["tags"]:
            phase["concomitant_injury_notes"].append(action["action_id"])
    for phase in phases:
        for key, value in phase.items():
            if isinstance(value, list) and key != "links_to_subprograms":
                phase[key] = list(dict.fromkeys(value))
        phase["page_numbers"] = sorted(phase["page_numbers"])
        phase["source_pages"] = sorted(phase["source_pages"])
    return actions, phases


def find_references(pages: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    references: list[dict[str, Any]] = []
    active = False
    for page in pages:
        for item in page["text_blocks"]:
            if item["heading_kind"] == "references":
                active = True
                continue
            if active and item["heading_kind"] in {"subprogram_running", "subprogram_agility_plyometrics"}:
                active = False
            if active and item["text"]:
                references.append({"page": page["page_number"], "source_element_id": item["element_id"], "text": item["text"]})
    return references


def write_report(output_dir: Path, document: dict[str, Any], pages: list[dict[str, Any]], actions: list[dict[str, Any]], phases: list[dict[str, Any]], references: list[dict[str, Any]]) -> None:
    table_count = sum(len(page["tables"]) for page in pages)
    link_count = sum(len(page["hyperlinks"]) for page in pages)
    text_count = sum(len(page["text_blocks"]) for page in pages)
    lines = [
        "# Raport diagnostyczny ekstrakcji protokołu rehabilitacyjnego",
        "",
        "## Zakres",
        "",
        f"- Identyfikator źródła: `{document['source_id']}`",
        f"- Plik lokalny: `{document['local_filename']}`",
        f"- SHA-256: `{document['sha256']}`",
        f"- Strony: {document['page_count']}",
        f"- Bloki tekstowe: {text_count}",
        f"- Wykryte tabele: {table_count}",
        f"- Adnotacje hiperłączy: {link_count}",
        f"- Rozpoznane fazy: {len(phases)}",
        f"- Kandydaci działań do audytu: {len(actions)}",
        f"- Wiersze referencji: {len(references)}",
        "",
        "## Co odzyskano",
        "",
        "- Kolejność bloków tekstowych na stronie wraz z pozycją, wielkością i nazwą fontu.",
        "- Wykryte tabele jako wiersze i komórki; tekst tabel może powtarzać się w blokach strony.",
        "- Adnotacje hiperłączy obecne w pliku PDF.",
        "- Mechanicznie rozpoznane etykiety faz i kategorii oraz inventory kandydatów działań.",
        "",
        "## Ograniczenia",
        "",
        "- OCR nie był używany. Elementy będące wyłącznie obrazem nie są opisane semantycznie.",
        "- Kolejność tekstu wynika z pozycji słów w PDF; wielokolumnowe i złożone układy wymagają kontroli wizualnej.",
        "- Wykrywanie tabel przez pdfplumber jest heurystyczne i może dzielić lub scalać komórki inaczej niż autor dokumentu.",
        "- Inventory zawiera mechanicznie zebrane kandydaty działań; nie jest audytem dowodów, nie ocenia poprawności i może wymagać ręcznego scalenia łamanych punktów.",
        "- Kategorie oraz powiązanie z fazą wynikają z widocznych nagłówków; nie należy ich traktować jako interpretacji klinicznej.",
    ]
    (output_dir / "diagnostic_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_pdf", type=Path, help="Lokalny PDF źródłowy.")
    parser.add_argument("output_dir", type=Path, help="Katalog roboczych wyników.")
    parser.add_argument("--source-id", required=True, help="Stabilny identyfikator źródła, np. mgh-aclr.")
    args = parser.parse_args()

    input_pdf = args.input_pdf.resolve()
    output_dir = args.output_dir.resolve()
    if not input_pdf.is_file():
        parser.error(f"Nie znaleziono pliku PDF: {input_pdf}")
    output_dir.mkdir(parents=True, exist_ok=True)

    document = {
        "source_id": args.source_id,
        "local_filename": input_pdf.name,
        "sha256": sha256(input_pdf),
        "extracted_at": datetime.now(UTC).isoformat(),
        "ocr_used": False,
        "extractor": "pdfplumber",
        "schema_version": SCHEMA_VERSION,
    }
    pages: list[dict[str, Any]] = []
    with pdfplumber.open(input_pdf) as pdf:
        document["page_count"] = len(pdf.pages)
        for page_number, page in enumerate(pdf.pages, start=1):
            lines = group_words_into_lines(page, page_number)
            pages.append(
                {
                    "page_number": page_number,
                    "size": {"width": round(float(page.width), 2), "height": round(float(page.height), 2)},
                    "text_blocks": [serialise_line(line, ordinal) for ordinal, line in enumerate(lines, start=1)],
                    "headings": [
                        {"text": line.text, "reading_order": line.reading_order, "kind": heading_kind(line.text)}
                        for line in lines if heading_kind(line.text) is not None
                    ],
                    "tables": extract_tables(page, page_number),
                    "hyperlinks": extract_hyperlinks(page, page_number),
                }
            )

    actions, phases = collect_actions(pages, args.source_id)
    references = find_references(pages)
    pages_payload = {"document": document, "pages": pages}
    structure = {
        "document": document,
        "general_components": [
            {"page": page["page_number"], "heading": heading}
            for page in pages for heading in page["headings"]
            if heading["kind"] not in {None, "phase"}
        ],
        "references": references,
        "limitations": [
            "Rozpoznawanie struktury jest mechaniczne i nie stanowi oceny klinicznej.",
            "Tabele i łamane punkty wymagają kontroli wizualnej przed późniejszym audytem.",
        ],
    }
    json_dump(output_dir / "pages.json", pages_payload)
    json_dump(output_dir / "protocol_structure.json", structure)
    json_dump(output_dir / "phase_map.json", {"document": document, "phases": phases})
    json_dump(output_dir / "action_inventory.json", {"document": document, "actions": actions})
    write_report(output_dir, document, pages, actions, phases, references)
    print(f"Wyodrębniono {document['page_count']} stron, {len(phases)} faz i {len(actions)} kandydatów działań.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
