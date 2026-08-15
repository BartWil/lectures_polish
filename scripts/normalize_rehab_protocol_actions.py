#!/usr/bin/env python3
"""Normalizuje inventory działań protokołu bez oceny dowodów klinicznych.

Oryginalny rekord i jego provenance pozostają nienaruszone. Skrypt dodaje
wyłącznie warstwę organizacyjną do planowania późniejszego action-level audit:
rodzinę działania, priorytet, testowalność, grupę duplikatów i pytanie
badawcze. Nie przeszukuje internetu i nie rozstrzyga poprawności zaleceń.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


FAMILY_LABELS = {
    "weight_bearing": "Obciążanie kończyny",
    "brace": "Orteza",
    "ROM": "Zakres ruchu",
    "swelling_pain_response": "Odpowiedź bólowo-wysiękowa",
    "strength": "Trening siłowy",
    "exercise_selection": "Dobór ćwiczeń",
    "exercise_dose": "Dawka i harmonogram ćwiczeń",
    "neuromuscular_control": "Kontrola nerwowo-mięśniowa",
    "balance": "Równowaga i propriocepcja",
    "cardiovascular": "Aktywność aerobowa",
    "running": "Bieganie",
    "plyometrics": "Plyometria",
    "agility": "Agility i trening specyficzny dla sportu",
    "strength_testing": "Testowanie siły",
    "hop_testing": "Testy skokowe",
    "PROM": "Wyniki zgłaszane przez pacjenta",
    "progression_criterion": "Kryterium progresji",
    "RTS": "Powrót do sportu",
    "physician_clearance": "Zgoda lekarza",
    "graft_specific": "Modyfikacja zależna od przeszczepu",
    "concomitant_procedure": "Modyfikacja zależna od procedury współistniejącej",
    "other": "Inne lub operacyjne",
}

QUESTION_TEMPLATES = {
    "weight-bearing-progression": (
        "Obciążanie kończyny po ACLR", "Jakie warunki i ograniczenia powinny kierować progresją obciążania po rekonstrukcji ACL?"
    ),
    "brace-management": (
        "Stosowanie ortezy", "Jakie są przesłanki dla blokowania, odblokowania i odstawienia ortezy po ACLR?"
    ),
    "early-extension-protection": (
        "Wczesna ochrona wyprostu", "Jakie ograniczenia wczesnego wyprostu i aktywacji mięśnia czworogłowego są uzasadnione po ACLR?"
    ),
    "rom-recovery": (
        "Odzyskiwanie zakresu ruchu", "Jak należy monitorować i progresować odzyskiwanie wyprostu oraz zgięcia po ACLR?"
    ),
    "swelling-pain-response": (
        "Ból i wysięk jako odpowiedź na obciążenie", "Jak objawy bólu, wysięku lub obrzęku powinny wpływać na progresję rehabilitacji po ACLR?"
    ),
    "early-functional-criteria": (
        "Wczesne kryteria funkcjonalne", "Jakie kryteria funkcjonalne są użyteczne przed przejściem z wczesnej fazy ACLR?"
    ),
    "strength-exercise-selection": (
        "Dobór treningu siłowego", "Jakie zasady doboru i progresji ćwiczeń siłowych stosować w rehabilitacji po ACLR?"
    ),
    "open-chain-knee-extension": (
        "Ćwiczenia wyprostu kolana w otwartym łańcuchu", "Jak dobierać zakres i progresję ćwiczeń wyprostu kolana w otwartym łańcuchu po ACLR?"
    ),
    "neuromuscular-balance": (
        "Kontrola nerwowo-mięśniowa i równowaga", "Jaką rolę oraz jakie kryteria progresji mają trening kontroli nerwowo-mięśniowej i równowagi po ACLR?"
    ),
    "cardiovascular-activity": (
        "Aktywność aerobowa", "Jak dobierać aktywność aerobową w kolejnych etapach rehabilitacji po ACLR?"
    ),
    "running-initiation": (
        "Rozpoczęcie biegania", "Jakie kryteria powinny poprzedzać rozpoczęcie programu powrotu do biegania po ACLR?"
    ),
    "running-progression": (
        "Progresja biegania", "Jak planować progresję objętości i intensywności biegania po ACLR?"
    ),
    "plyometric-initiation": (
        "Rozpoczęcie plyometrii", "Jakie kryteria powinny poprzedzać progresję do plyometrii po ACLR?"
    ),
    "agility-progression": (
        "Progresja agility", "Jak progresować zadania agility i wielopłaszczyznowe po ACLR?"
    ),
    "strength-thresholds": (
        "Progi siły", "Jak interpretować progi siły i symetrii przy progresji po ACLR?"
    ),
    "hop-thresholds": (
        "Progi testów skokowych", "Jak interpretować progi testów skokowych przy progresji i powrocie do sportu po ACLR?"
    ),
    "prom-thresholds": (
        "Progi PROM", "Jaką rolę mają progi wyników zgłaszanych przez pacjenta w progresji po ACLR?"
    ),
    "rts-decision": (
        "Decyzja o powrocie do sportu", "Jak łączyć kryteria czasowe, funkcjonalne i specyficzne dla sportu w decyzji RTS po ACLR?"
    ),
    "physician-clearance": (
        "Zgoda lekarza", "W jakich punktach progresji konieczna jest decyzja lub zgoda lekarza prowadzącego?"
    ),
    "graft-modifications": (
        "Modyfikacje zależne od przeszczepu", "Jak typ przeszczepu powinien modyfikować ograniczenia i tempo progresji po ACLR?"
    ),
    "concomitant-modifications": (
        "Modyfikacje przy procedurach współistniejących", "Jak procedury lub urazy współistniejące powinny zmieniać rehabilitację po ACLR?"
    ),
    "time-as-context": (
        "Czas jako kontekst progresji", "Jak łączyć ramy czasowe z kryteriami funkcjonalnymi w rehabilitacji po ACLR?"
    ),
    "protocol-administration": (
        "Elementy operacyjne", "Element nie stanowi samodzielnego pytania evidence; zachować tylko jako kontekst protokołu."
    ),
}

RESEARCH_BLOCKS = {
    "weight-bearing-progression": "A — wczesna rehabilitacja",
    "brace-management": "A — wczesna rehabilitacja",
    "early-extension-protection": "A — wczesna rehabilitacja",
    "rom-recovery": "A — wczesna rehabilitacja",
    "swelling-pain-response": "A — wczesna rehabilitacja",
    "early-functional-criteria": "A — wczesna rehabilitacja",
    "graft-modifications": "A — wczesna rehabilitacja",
    "concomitant-modifications": "A — wczesna rehabilitacja",
    "strength-exercise-selection": "B — siła i obciążanie rehabilitacyjne",
    "open-chain-knee-extension": "B — siła i obciążanie rehabilitacyjne",
    "neuromuscular-balance": "B — siła i obciążanie rehabilitacyjne",
    "cardiovascular-activity": "B — siła i obciążanie rehabilitacyjne",
    "time-as-context": "B — siła i obciążanie rehabilitacyjne",
    "running-initiation": "C — powrót do biegania i plyometrii",
    "running-progression": "C — powrót do biegania i plyometrii",
    "plyometric-initiation": "C — powrót do biegania i plyometrii",
    "agility-progression": "C — powrót do biegania i plyometrii",
    "strength-thresholds": "C — powrót do biegania i plyometrii",
    "hop-thresholds": "D — powrót do sportu",
    "prom-thresholds": "D — powrót do sportu",
    "rts-decision": "D — powrót do sportu",
    "physician-clearance": "D — powrót do sportu",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def contains(text: str, *terms: str) -> bool:
    return any(term in text for term in terms)


def family_and_concept(action: dict[str, Any]) -> tuple[str, str]:
    text = action["normalized_action"].casefold()
    category = (action.get("category") or "").casefold()
    source_type = action.get("source_type") or ""

    if text.endswith(":") and "single leg" in text:
        return "other", "protocol-administration"
    if re.match(r"^\d+\.\s+.+\b(?:journal|am j sports med|med sci sports exerc)\b", text):
        return "other", "protocol-administration"
    if contains(text, "allograft", "autograft", "graft donor"):
        return "graft_specific", "graft-modifications"
    if contains(text, "meniscus repair", "concomitant"):
        return "concomitant_procedure", "concomitant-modifications"
    if contains(text, "clearance from md", "clearance from", "referring physician", "referring surgeon"):
        return "physician_clearance", "physician-clearance"
    if contains(text, "koos", "acl-rsi", "international knee documentation", "psych readiness", "prrs"):
        return "PROM", "prom-thresholds"
    if "hop testing" in text:
        return "hop_testing", "hop-thresholds"
    if contains(text, "hops over", "drop vertical jump"):
        return "plyometrics", "plyometric-initiation"
    if contains(text, "quad/hs/glut index", "quadriceps index", "hamstrings ≥", "hamstring/quad ratio", "isokinetic", " hhd"):
        return "strength_testing", "strength-thresholds"
    if contains(text, "weight bearing", "partial weight bearing", "crutches"):
        return "weight_bearing", "weight-bearing-progression"
    if contains(text, "progress to plyometric", "plyometric and agility"):
        return "plyometrics", "plyometric-initiation"
    if "brace" in text:
        return "brace", "brace-management"
    if contains(text, "knee extension lag", "do not actively kick", "straight leg raise"):
        return "ROM", "early-extension-protection"
    if contains(text, "full active extension", "maintain full rom"):
        return "ROM", "rom-recovery"
    if contains(text, "range of motion", " rom ", "flexion rom", "extension rom", "full extension", "full flexion", "patellar mobilization"):
        return "ROM", "rom-recovery"
    if contains(text, "leg extension", "quad sets", "squat", "leg press", "deadlift", "hamstring curl", "calf raise", "lunge", "step up", "strengthening"):
        return "strength", "strength-exercise-selection"
    if contains(text, "effusion", "swelling", "pain", "modified stroke test"):
        return "swelling_pain_response", "swelling-pain-response"
    if contains(text, "elliptical", "stair climber", "swimming", "pool jogging", "bicycle", "cardio"):
        return "cardiovascular", "cardiovascular-activity"
    if contains(text, "patients should demonstrate", "prior to initiating"):
        return "progression_criterion", "early-functional-criteria"
    if contains(text, "return to run", "interval running", "jog/run", "mileage", "running program", "/j"):
        return "running", "running-progression" if contains(text, "mileage", "week", "day", "/j") else "running-initiation"
    if contains(text, "return to sport", "full play", "full practice", "hard cutting", "pivoting"):
        return "RTS", "rts-decision"
    if contains(text, "plyometric", "jump", "hops", "bounding", "shuttle press"):
        return "plyometrics", "plyometric-initiation"
    if contains(text, "agility", "shuttle run", "zig-zag", "carioca", "ladder", "box drill", "star drill"):
        return "agility", "agility-progression"
    if contains(text, "balance", "proprioception", "joint position", "perturbation"):
        return "balance", "neuromuscular-balance"
    if source_type == "table_row" or category == "table_schedule":
        return "exercise_dose", "time-as-context"
    if category == "criteria_to_progress" or contains(text, "proper movement", "normal gait", "no episodes of instability"):
        return "progression_criterion", "early-functional-criteria"
    if category in {"goals", "other"} or source_type == "normative_text":
        return "other", "protocol-administration"
    return "exercise_selection", "strength-exercise-selection"


def priority(family: str, concept: str, action: dict[str, Any]) -> tuple[str, str, str, str]:
    text = action["normalized_action"].casefold()
    if family in {
        "weight_bearing", "brace", "ROM", "strength_testing", "hop_testing", "PROM",
        "RTS", "physician_clearance", "graft_specific", "concomitant_procedure",
    } or (family == "swelling_pain_response" and action.get("phase")):
        return "Tier A", "directly_testable" if family in {"strength_testing", "hop_testing", "PROM"} else "indirectly_supported", "high", "yes"
    if family == "progression_criterion":
        return "Tier A", "indirectly_supported", "high", "yes"
    if family in {"strength", "exercise_selection", "neuromuscular_control", "balance", "cardiovascular", "running", "plyometrics", "agility", "exercise_dose"}:
        testability = "protocol_convention" if family == "exercise_dose" or re.search(r"\b(?:day|week|month|\d+\s*(?:min|reps|sets))\b", text) else "indirectly_supported"
        return "Tier B", testability, "moderate", "yes"
    return "Tier C", "not_evidence_question" if concept == "protocol-administration" else "insufficiently_specific", "low", "no"


def suggested_evidence_type(tier: str, family: str) -> str:
    if tier == "Tier A":
        if family in {"strength_testing", "hop_testing", "PROM", "RTS"}:
            return "wytyczne lub konsensus RTS; przeglądy systematyczne dotyczące kryteriów"
        if family in {"graft_specific", "concomitant_procedure"}:
            return "wytyczne procedurowe, konsensus oraz badania dla konkretnej procedury"
        return "wytyczne kliniczne, konsensus i przeglądy systematyczne"
    if tier == "Tier B":
        return "przeglądy systematyczne; badania porównawcze, jeśli istnieją"
    return "brak odrębnego researchu; zachować jako kontekst lub decyzję programistyczną"


def manual_review(action: dict[str, Any], family: str) -> tuple[bool, str | None]:
    text = action["normalized_action"]
    if text.casefold().startswith("*continue with"):
        return True, "Punkt zawiera sklejony znacznik kontynuacji; wymaga weryfikacji względem układu źródłowego."
    if action.get("source_type") == "table_row":
        return True, "Harmonogram tabelaryczny wymaga sprawdzenia relacji wiersz–kolumna przed audytem."
    if family == "other":
        return True, "Treść jest zbyt ogólna, administracyjna albo łamana na wiersze; wymaga decyzji o zakresie audytu."
    if re.search(r"\b(?:W\d+/J\d+|DL|FWB|PWB)\b", text):
        return True, "Skrót lub zapis programu wymaga ręcznego odczytu legendy źródłowej."
    return False, None


def is_threshold_record(record: dict[str, Any]) -> bool:
    text = record["normalized_action"].casefold()
    if record["timing_or_timeframe"] or record["criterion_or_threshold"]:
        return any(
            not str(value).casefold().startswith("within this guideline")
            for value in record["criterion_or_threshold"]
        ) or bool(record["timing_or_timeframe"])
    return bool(re.search(
        r"(?:\b\d+(?:\.\d+)?\s*(?:%|deg|weeks?|months?|days?|min)\b|"
        r"\b(?:no|normal|full|equal)\b.{0,45}\b(?:pain|swelling|effusion|gait|rom|extension|flexion)\b|"
        r"\b(?:clearance|functional assessment)\b)",
        text,
    ))


def threshold_type(family: str) -> str:
    return {
        "ROM": "ROM_threshold",
        "strength_testing": "strength_threshold",
        "hop_testing": "hop_threshold",
        "PROM": "PROM_threshold",
        "running": "running_criterion_or_time",
        "RTS": "RTS_criterion_or_time",
        "progression_criterion": "progression_criterion",
        "weight_bearing": "time_or_weight_bearing_threshold",
        "brace": "brace_criterion_or_time",
    }.get(family, "time_threshold")


def evidence_audit_template(
    document: dict[str, Any],
    questions: list[dict[str, Any]],
    thresholds: list[dict[str, Any]],
    normalized_records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Tworzy pusty, śledzalny szablon decyzji do późniejszego evidence audit.

    Ten etap nie dodaje żadnych źródeł ani odpowiedzi klinicznych. Pola
    decyzyjne pozostają puste, aby nie mieszać opisu MGH z przyszłym naszym
    protokołem.
    """
    thresholds_by_action: dict[str, list[str]] = defaultdict(list)
    for threshold in thresholds:
        thresholds_by_action[threshold["original_action_id"]].append(threshold["threshold_id"])

    records: list[dict[str, Any]] = []
    for question in questions:
        concept = next(
            (
                record["normalized_concept"]
                for record in normalized_records
                if record["action_id"] in question["linked_actions"]
            ),
            None,
        )
        if concept is None or concept not in RESEARCH_BLOCKS:
            raise ValueError(f"Brak przypisanego bloku researchu dla {question['question_id']}.")
        records.append(
            {
                "question_id": question["question_id"],
                "research_block": RESEARCH_BLOCKS[concept],
                "clinical_question": question["clinical_question"],
                "linked_actions": question["linked_actions"],
                "linked_thresholds": [
                    threshold_id
                    for action_id in question["linked_actions"]
                    for threshold_id in thresholds_by_action[action_id]
                ],
                "phases": question["phases"],
                "evidence_priority": question["evidence_priority"],
                "evidence_status": None,
                "evidence_certainty": None,
                "source_hierarchy": [],
                "evidence_summary": None,
                "limitations": [],
                "mgh_assessment": None,
                "proposed_protocol_decision": None,
                "decision_rationale": None,
            }
        )
    return {
        "document": document,
        "purpose": "Pusty szablon action-level evidence audit; nie zawiera wyników researchu.",
        "allowed_values": {
            "evidence_status": [
                "empirically_supported", "consensus_supported", "indirectly_supported",
                "context_dependent", "protocol_convention", "insufficient_evidence", "contradicted",
            ],
            "evidence_certainty": ["high", "moderate", "low", "very_low", "not_applicable"],
            "mgh_assessment": ["keep", "modify", "remove", "context_dependent"],
        },
        "questions": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory", type=Path, help="action_inventory.json z extract_rehab_protocol_pdf.py")
    parser.add_argument("output_dir", type=Path, help="Katalog roboczych wyników")
    parser.add_argument("--question-prefix", default="ACL-EQ", help="Prefiks identyfikatorów pytań")
    args = parser.parse_args()

    source = read_json(args.inventory)
    actions = source.get("actions", [])
    if not actions:
        parser.error("Inventory nie zawiera actions.")
    normalized: list[dict[str, Any]] = []
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for action in actions:
        family, concept = family_and_concept(action)
        tier, testability, risk, audit = priority(family, concept, action)
        needs_review, review_reason = manual_review(action, family)
        record = dict(action)
        record.update(
            {
                "normalized_concept": concept,
                "action_family": family,
                "evidence_priority": tier,
                "evidence_testability": testability,
                "duplicate_group": None,
                "protocol_specificity": "high" if action.get("timing_or_timeframe") or action.get("criterion_or_threshold") else "moderate",
                "clinical_risk": risk,
                "future_audit_required": audit,
                "requires_manual_review": needs_review,
                "manual_review_reason": review_reason,
            }
        )
        groups[concept].append(record)
        normalized.append(record)

    question_groups: list[dict[str, Any]] = []
    question_number = 0
    for number, (concept, records) in enumerate(sorted(groups.items()), start=1):
        duplicate_id = f"ACL-DUP-{number:03d}"
        for record in records:
            record["duplicate_group"] = duplicate_id
        tiers = {record["evidence_priority"] for record in records}
        tier = "Tier A" if "Tier A" in tiers else "Tier B" if "Tier B" in tiers else "Tier C"
        family = records[0]["action_family"]
        if tier == "Tier C":
            continue
        question_number += 1
        topic, question = QUESTION_TEMPLATES[concept]
        question_groups.append(
            {
                "question_id": f"{args.question_prefix}-{question_number:03d}",
                "topic": topic,
                "clinical_question": question,
                "linked_actions": [record["action_id"] for record in records],
                "phases": sorted({record["phase"] for record in records if record.get("phase")}),
                "evidence_priority": tier,
                "suggested_evidence_type": suggested_evidence_type(tier, family),
                "notes": "Pytanie utworzone podczas normalizacji; nie zawiera odpowiedzi ani oceny zalecenia.",
            }
        )

    thresholds: list[dict[str, Any]] = []
    for record in normalized:
        if not is_threshold_record(record):
            continue
        thresholds.append(
            {
                "threshold_id": f"ACL-THR-{len(thresholds) + 1:03d}",
                "threshold_type": threshold_type(record["action_family"]),
                "original_action_id": record["action_id"],
                "phase": record["phase"],
                "page": record["source_page"],
                "original_context": record["original_context"],
                "source_text": record["normalized_action"],
                "timing_or_timeframe": record["timing_or_timeframe"],
                "criterion_or_threshold": record["criterion_or_threshold"],
                "duplicate_group": record["duplicate_group"],
                "future_evidence_audit_required": record["future_audit_required"],
            }
        )

    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    document = source.get("document", {})
    audit_template = evidence_audit_template(document, question_groups, thresholds, normalized)
    dump_json(out / "action_inventory_normalized.json", {"document": document, "actions": normalized})
    dump_json(out / "evidence_questions.json", {"document": document, "questions": question_groups})
    dump_json(out / "threshold_inventory.json", {"document": document, "thresholds": thresholds})
    dump_json(out / "evidence_audit_template.json", audit_template)
    print(f"Znormalizowano {len(normalized)} działań do {len(question_groups)} grup pytań; progów: {len(thresholds)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
