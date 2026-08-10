#!/usr/bin/env python3
"""Tworzy lokalny blueprint treści z zatwierdzonego visual triage.

To narzędzie planistyczne nie tworzy QMD, nie przenosi obrazów i nie zmienia
źródłowej prezentacji. Wynik pozostaje w ``imports_working/``.
"""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKING_ROOT = PROJECT_ROOT / "imports_working"
PRESENTATION = "WYKŁAD_1_2_Podstawy_traumatologia_Złamania_Skręcenia"


def page(
    page_id: str, title: str, scope: str, primary: list[int], supporting: list[int], available: str,
    completeness: str, missing: str, redundancy: str, visual: list[dict[str, Any]], risk: str,
    sensitive: list[int], review: str, reason: str, forms: list[str],
) -> dict[str, Any]:
    return {
        "page_id": page_id,
        "provisional_title_pl": title,
        "scope": scope,
        "source_slides": sorted(set(primary + supporting)),
        "primary_source_slides": primary,
        "supporting_source_slides": supporting,
        "available_content": available,
        "source_only_completeness": completeness,
        "missing_or_thin_content": missing,
        "redundancy": redundancy,
        "visual_assets": visual,
        "image_rights_risk": risk,
        "potential_sensitive_content": sensitive,
        "manual_content_review_required": review,
        "manual_content_review_reason": reason,
        "recommended_content_form": forms,
    }


PAGES = [
    page("traumatology-foundations", "Podstawy traumatologii narządu ruchu",
         "Definicja urazu, zakres uszkodzeń narządu ruchu i ogólne następstwa tkankowe.", [29, 30, 31, 32], [],
         "Definicja, zakres urazów i opis odpowiedzi tkankowej.", "medium",
         "Brak samodzielnego, rozwiniętego porównania mechanizmów i ograniczone przykłady.",
         "Slajdy 29–32 częściowo powtarzają wprowadzenie; zachować jako źródła, nie scalać automatycznie.",
         [{"slide_number": 29, "type": "clinical_photo", "role": "wprowadzenie", "needed": "optional", "replace_with_original_graphic": "yes", "rights_review": "yes", "sensitive_review": "yes"}],
         "high", [29], "yes", "Fotografie i widoczne cytowanie wymagają odrębnej kontroli przed użyciem publicznym.",
         ["definition", "narrative_text", "key_points"]),
    page("healing-and-rehabilitation-principles", "Gojenie po urazie i zasady rehabilitacji",
         "Fazy gojenia, mechanotransdukcja oraz ogólne zasady postępowania rehabilitacyjnego.", [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 26, 27], [8, 9, 21, 22, 23, 24, 25],
         "Fazy gojenia, opis tkanek, zasady rehabilitacji i tabela porządkująca etapy.", "high",
         "Ograniczone wyjaśnienie granic zastosowania oraz zależności od typu urazu; slajdy nie tworzą pełnego algorytmu.",
         "Sekwencje 12–14 i 21–27 są częściowo powtarzalne; tabela 26 może zastąpić wielokrotne powtórzenia w przyszłej redakcji.",
         [{"slide_number": 11, "type": "chart", "role": "fazy gojenia", "needed": "yes", "replace_with_original_graphic": "yes", "rights_review": "yes", "sensitive_review": "no"}, {"slide_number": 17, "type": "chart", "role": "czasowy schemat rehabilitacji", "needed": "yes", "replace_with_original_graphic": "yes", "rights_review": "yes", "sensitive_review": "no"}, {"slide_number": 24, "type": "multiple_images", "role": "przykłady ćwiczeń", "needed": "optional", "replace_with_original_graphic": "yes", "rights_review": "yes", "sensitive_review": "yes"}],
         "high", [24, 25], "yes", "Wykresy i fotografie wymagają audytu źródeł; tabela 26 wymaga ręcznej redakcji układu.",
         ["narrative_text", "comparison_table", "clinical_algorithm", "figure_needed", "key_points"]),
    page("fracture-mechanisms-and-classification", "Złamania: mechanizmy i klasyfikacja",
         "Podstawowe pojęcia, etiologia, patogeneza, objawy i klasyfikacja złamań, w tym podział złamań otwartych.", [33, 36, 38, 40, 42, 48, 49, 50, 51, 53, 54], [34, 35, 39, 41, 52],
         "Pojęcia, klasyfikacje, objawy, różnicowanie i profilaktyka; dostępne są schematy typów złamań.", "high",
         "Materiał nie zawiera spójnego, tekstowego połączenia wszystkich klasyfikacji ze wskazaniami praktycznymi.",
         "48–49 są duplikatem; 34–35 oraz 38–41 przedstawiają blisko powiązane ujęcia mechanizmów.",
         [{"slide_number": 34, "type": "anatomy_illustration", "role": "typy złamań", "needed": "yes", "replace_with_original_graphic": "yes", "rights_review": "yes", "sensitive_review": "no"}, {"slide_number": 35, "type": "anatomy_illustration", "role": "porównanie typów", "needed": "optional", "replace_with_original_graphic": "yes", "rights_review": "yes", "sensitive_review": "no"}, {"slide_number": 52, "type": "radiograph", "role": "przykład obrazowy", "needed": "optional", "replace_with_original_graphic": "yes", "rights_review": "yes", "sensitive_review": "yes"}],
         "high", [52], "yes", "Ryciny i RTG nie mogą być przeniesione bez audytu; większość materiału tekstowego jest wystarczająca.",
         ["definition", "narrative_text", "comparison_table", "figure_needed", "key_points"]),
    page("fracture-imaging-and-diagnosis", "Złamania: diagnostyka obrazowa",
         "Zakres badań dodatkowych i przykłady obrazowania w prezentacji.", [37, 43, 44, 45, 46, 47, 52], [],
         "Nazwy badań dodatkowych oraz jeden rozbudowany przykład wielomodalnego obrazowania.", "medium",
         "Brak pełnego schematu decyzji, kryteriów doboru badania i jednolitego opisu przypadków.",
         "Slajdy 43–47 tworzą serię uzupełniającą; nie są duplikatami, lecz wymagają wspólnej redakcji.",
         [{"slide_number": 37, "type": "radiograph/MRI", "role": "przypadek obrazowania", "needed": "optional", "replace_with_original_graphic": "yes", "rights_review": "yes", "sensitive_review": "yes"}, {"slide_number": 52, "type": "radiograph", "role": "przykład", "needed": "optional", "replace_with_original_graphic": "yes", "rights_review": "yes", "sensitive_review": "yes"}],
         "high", [37, 52], "yes", "Obrazy diagnostyczne i opis przypadku wymagają kontroli źródła, praw i potencjalnej wrażliwości danych.",
         ["narrative_text", "comparison_table", "clinical_algorithm", "warning_box"]),
    page("fracture-treatment-principles", "Złamania: zasady leczenia",
         "Unieruchomienie, repozycja, wskazania do leczenia operacyjnego i podstawowe metody zespolenia.", [55, 56, 57, 58, 59, 60, 61, 72, 73, 74, 75, 76, 77], [62, 78],
         "Opis leczenia nieoperacyjnego i operacyjnego, wskazań, metod zespolenia oraz rokowania.", "high",
         "Materiał nie zawiera kompletnego algorytmu wyboru metody ani jednolitej tabeli porównawczej.",
         "60–62 i 72–76 dotyczą metod zespolenia, ale zawierają odmienne aspekty; wymagają syntetycznej redakcji.",
         [{"slide_number": 61, "type": "radiograph", "role": "przykład stabilizacji", "needed": "optional", "replace_with_original_graphic": "yes", "rights_review": "yes", "sensitive_review": "yes"}, {"slide_number": 76, "type": "radiograph", "role": "przykład drutów Kirschnera", "needed": "optional", "replace_with_original_graphic": "yes", "rights_review": "yes", "sensitive_review": "yes"}, {"slide_number": 78, "type": "clinical_illustration", "role": "przykład historyczny", "needed": "no", "replace_with_original_graphic": "yes", "rights_review": "yes", "sensitive_review": "no"}],
         "high", [61, 62, 76], "yes", "Obrazy i zewnętrzne odnośniki wymagają audytu; zasadniczy tekst jest kandydatem do redakcji bez kopiowania obrazów.",
         ["narrative_text", "comparison_table", "clinical_algorithm", "key_points"]),
    page("femur-fractures", "Wybrane złamania: kość udowa",
         "Przykłady złamań trzonu i dalszej części kości udowej, metody stabilizacji oraz przykłady przypadków.", [63, 64, 65, 66, 67, 68, 69, 70, 71], [],
         "Opis problemów, metod stabilizacji i kilka przykładów obrazowych/przypadków.", "medium",
         "Brak kompletnego, samodzielnego opisu zakresu, kryteriów wyboru i spójnego toku przypadku.",
         "66–71 są sekwencją przykładów, nie prostymi duplikatami; należy zachować relację tekst–obraz.",
         [{"slide_number": 66, "type": "radiograph/diagram", "role": "przykład rozpoznania", "needed": "optional", "replace_with_original_graphic": "yes", "rights_review": "yes", "sensitive_review": "yes"}, {"slide_number": 68, "type": "multiple_radiographs", "role": "kolejne etapy", "needed": "optional", "replace_with_original_graphic": "yes", "rights_review": "yes", "sensitive_review": "yes"}, {"slide_number": 71, "type": "radiograph/CT", "role": "przykład leczenia", "needed": "optional", "replace_with_original_graphic": "yes", "rights_review": "yes", "sensitive_review": "yes"}],
         "high", [66, 68, 71], "yes", "Duża zależność od obrazów i przypadków oraz podwyższone ryzyko wrażliwych danych.",
         ["narrative_text", "case_example", "figure_needed", "warning_box"]),
    page("olecranon-fractures", "Wybrane złamania: wyrostek łokciowy",
         "Złamania kości łokciowej/wyrostka łokciowego, anatomia funkcjonalna, leczenie i wyniki.", [79, 80, 81, 82, 83, 84, 85, 86], [],
         "Opis lokalizacji, funkcji, opcji leczenia i obrazowe przykłady zespolenia.", "medium",
         "Brak pełnej, tekstowej struktury rozpoznania i porównania metod leczenia.",
         "83–86 rozwijają jedną sekwencję terapeutyczną; nie usuwać bez ręcznej analizy.",
         [{"slide_number": 80, "type": "anatomy_illustration", "role": "punkty orientacyjne", "needed": "yes", "replace_with_original_graphic": "yes", "rights_review": "yes", "sensitive_review": "no"}, {"slide_number": 82, "type": "radiograph/diagram", "role": "mechanizm", "needed": "optional", "replace_with_original_graphic": "yes", "rights_review": "yes", "sensitive_review": "yes"}, {"slide_number": 85, "type": "radiograph", "role": "wynik leczenia", "needed": "optional", "replace_with_original_graphic": "yes", "rights_review": "yes", "sensitive_review": "yes"}],
         "high", [82, 85, 86], "yes", "Materiały obrazowe i ilustracje wymagają audytu; materiał źródłowy jest umiarkowanie kompletny.",
         ["narrative_text", "comparison_table", "figure_needed", "key_points"]),
    page("scaphoid-fractures", "Wybrane złamania: kość łódeczkowata",
         "Anatomia, objawy, badanie, obrazowanie i przykłady leczenia złamań kości łódeczkowatej.", [87, 88, 89, 90, 91, 92, 93, 94, 95, 96], [],
         "Ciąg obejmujący lokalizację, objawy, elementy badania, MR/RTG oraz leczenie.", "high",
         "Brak spójnego, pełnego algorytmu przechodzącego od podejrzenia do kontroli leczenia.",
         "87–96 tworzą sekwencję jednego tematu; część ilustracji anatomicznych powtarza funkcję orientacyjną.",
         [{"slide_number": 89, "type": "anatomy_illustration", "role": "orientacja anatomiczna", "needed": "yes", "replace_with_original_graphic": "yes", "rights_review": "yes", "sensitive_review": "no"}, {"slide_number": 94, "type": "MRI", "role": "przykład obrazowania", "needed": "optional", "replace_with_original_graphic": "yes", "rights_review": "yes", "sensitive_review": "yes"}, {"slide_number": 96, "type": "radiograph", "role": "przykład zespolenia", "needed": "optional", "replace_with_original_graphic": "yes", "rights_review": "yes", "sensitive_review": "yes"}],
         "high", [87, 88, 94, 96], "yes", "Wartość strony jest wysoka, lecz wszystkie obrazy wymagają osobnej decyzji publikacyjnej.",
         ["narrative_text", "clinical_algorithm", "comparison_table", "figure_needed", "key_points"]),
    page("sprain-basics", "Skręcenia: podstawy i rozpoznanie",
         "Definicja, częstość, różnicowanie, elementy rozpoznania i klasyfikacja skręceń.", [98, 99, 100, 101, 102, 105, 106, 107, 117], [103, 104],
         "Definicja, epidemiologia, diagnostyka, klasyfikacja i rokowanie; dwa slajdy wizualne pokazują uraz/ruch.", "high",
         "Brak wyraźnego schematu przejścia od oceny do postępowania oraz ograniczony opis obrazowania.",
         "101–107 są rozwinięciem jednego wątku, a nie kandydatami do strony na slajd.",
         [{"slide_number": 103, "type": "clinical_photo/anatomy_illustration", "role": "demonstracja", "needed": "optional", "replace_with_original_graphic": "yes", "rights_review": "yes", "sensitive_review": "yes"}, {"slide_number": 104, "type": "clinical_photo", "role": "demonstracja ruchu", "needed": "optional", "replace_with_original_graphic": "yes", "rights_review": "yes", "sensitive_review": "yes"}, {"slide_number": 106, "type": "anatomy_illustration", "role": "klasyfikacja", "needed": "yes", "replace_with_original_graphic": "yes", "rights_review": "yes", "sensitive_review": "no"}],
         "high", [103, 104], "yes", "Fotografie i ilustracje zewnętrzne nie powinny być kopiowane bez audytu.",
         ["definition", "narrative_text", "comparison_table", "clinical_algorithm", "key_points"]),
    page("ankle-anatomy-for-sprains", "Staw skokowy: anatomia przydatna w skręceniach",
         "Struktury anatomiczne stopy i stawu skokowego oraz więzadła istotne dla skręceń.", [108, 109, 110, 111, 112, 113, 114, 115, 116, 119, 120, 121, 122, 123, 124, 125, 126], [118],
         "Ilustracje struktur, nazwy więzadeł, unerwienie i relacje anatomiczne.", "medium",
         "Treść jest silnie obrazowa; sam tekst strukturalny jest zbyt skąpy do pełnej strony bez nowej autorskiej grafiki.",
         "108–116 oraz 121–126 zawierają podobne serie ilustracji; potrzebna późniejsza selekcja funkcji dydaktycznej.",
         [{"slide_number": 108, "type": "anatomy_illustration", "role": "orientacja", "needed": "yes", "replace_with_original_graphic": "yes", "rights_review": "yes", "sensitive_review": "no"}, {"slide_number": 110, "type": "anatomy_illustration/radiograph", "role": "relacje anatomiczne", "needed": "optional", "replace_with_original_graphic": "yes", "rights_review": "yes", "sensitive_review": "no"}, {"slide_number": 121, "type": "anatomy_illustration", "role": "więzadła", "needed": "yes", "replace_with_original_graphic": "yes", "rights_review": "yes", "sensitive_review": "no"}],
         "high", [], "yes", "Duże uzależnienie od zewnętrznych rycin; najlepszym kierunkiem są nowe grafiki autorskie.",
         ["narrative_text", "figure_needed", "comparison_table", "key_points"]),
    page("ankle-sprain-clinical-examination", "Skręcenie stawu skokowego: badanie kliniczne i przypadek",
         "Przypadkowe przykłady i demonstracje badania fizykalnego ze źródłowej prezentacji.", [127, 128, 129, 130, 131], [],
         "Sekwencja opisów przypadku i demonstracji badania.", "low",
         "Brak samodzielnego, wystarczająco pełnego tekstu; znaczenie slajdów zależy od fotografii.",
         "127–131 są etapami jednego przypadku/demonstracji; nie stanowią odrębnych stron.",
         [{"slide_number": 127, "type": "clinical_photo", "role": "przypadek", "needed": "no", "replace_with_original_graphic": "yes", "rights_review": "yes", "sensitive_review": "yes"}, {"slide_number": 130, "type": "clinical_photo", "role": "demonstracja testu", "needed": "no", "replace_with_original_graphic": "yes", "rights_review": "yes", "sensitive_review": "yes"}],
         "high", [127, 128, 129, 130, 131], "yes", "Fotografie mogą przedstawiać osoby; bez ich użycia materiał źródłowy jest zbyt cienki.",
         ["case_example", "figure_needed", "warning_box"]),
    page("dislocations", "Zwichnięcia: podstawy, rozpoznanie i leczenie",
         "Definicja, epidemiologia, etiologia, objawy, badania, klasyfikacja, profilaktyka, leczenie i rokowanie zwichnięć.", [132, 133, 134, 135, 136, 137, 138, 139, 140, 142, 143, 144, 145], [],
         "Ciąg tekstowych slajdów obejmujący pełny podstawowy zakres tematu.", "high",
         "Brak wartościowych, własnych materiałów wizualnych; odnośnik wideo nie jest zachowaną treścią.",
         "Tematy kolejnych slajdów są komplementarne; powtórzenia dotyczą głównie nagłówków, nie treści.", [],
         "low", [], "no", "Materiał jest głównie tekstowy; wideo 141 wymaga osobnej decyzji przy późniejszej redakcji.",
         ["definition", "narrative_text", "comparison_table", "clinical_algorithm", "key_points"]),
    page("ligament-injuries-introduction", "Uszkodzenia więzadeł: wprowadzenie",
         "Definicja, patomechanizm i podział uszkodzeń więzadeł; odnośnik wideo jako materiał źródłowy.", [146, 147], [],
         "Dwa tekstowe slajdy wprowadzające oraz sam URL do materiału zewnętrznego.", "low",
         "Brak rozwinięcia diagnostyki, leczenia, przykładów i bezpośrednio dostępnej treści wideo.",
         "146–147 są krótkim wprowadzeniem; nie należy tworzyć pełnej strony bez dalszego źródła materiału.", [],
         "low", [], "yes", "Odnośnik 148 jest treścią zewnętrzną, nie gotowym materiałem do publikacji.",
         ["definition", "narrative_text", "key_points"]),
]


UNUSED = {
    1: "administrative", 2: "administrative", 3: "administrative", 4: "administrative", 5: "administrative", 6: "source_only", 7: "source_only", 28: "transition", 97: "source_only", 141: "source_only", 148: "source_only",
}


def build_source_map() -> list[dict[str, Any]]:
    mapping: dict[int, list[str]] = {number: [] for number in range(1, 149)}
    for item in PAGES:
        for number in item["source_slides"]:
            mapping[number].append(item["page_id"])
    records = []
    for number in range(1, 149):
        page_ids = mapping[number]
        records.append({
            "slide_number": number,
            "future_knowledge_units": page_ids,
            "status": "used" if page_ids else "unused",
            "unused_reason": None if page_ids else UNUSED.get(number, "unclear"),
        })
    return records


def write_outputs(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    source_map = build_source_map()
    payload = {
        "schema_version": "1.0",
        "created_at": datetime.now(UTC).isoformat(),
        "hierarchy": {"subject_area": "PFK", "subject": "Ortopedia i traumatologia"},
        "presentation": PRESENTATION,
        "knowledge_units": PAGES,
        "source_map": source_map,
    }
    (destination / "content_blueprint.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    columns = ["page_id", "provisional_title_pl", "source_slides", "primary_source_slides", "supporting_source_slides", "source_only_completeness", "image_rights_risk", "potential_sensitive_content", "manual_content_review_required", "recommended_content_form", "scope", "missing_or_thin_content", "redundancy"]
    with (destination / "content_blueprint.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for item in PAGES:
            row = dict(item)
            for key in ("source_slides", "primary_source_slides", "supporting_source_slides", "potential_sensitive_content", "recommended_content_form"):
                row[key] = "; ".join(str(value) for value in row[key])
            writer.writerow({key: row[key] for key in columns})
    markdown = ["# Content blueprint", "", "Robocza hierarchia: `PFK → Ortopedia i traumatologia → jednostki wiedzy`.", "", "Nie jest to struktura stron Quarto ani treść dydaktyczna.", ""]
    for item in PAGES:
        markdown.extend([
            f"## {item['provisional_title_pl']} (`{item['page_id']}`)",
            f"- Zakres: {item['scope']}",
            f"- Slajdy źródłowe: {', '.join(map(str, item['source_slides']))}",
            f"- Główne / wspierające: {', '.join(map(str, item['primary_source_slides']))} / {', '.join(map(str, item['supporting_source_slides'])) or '—'}",
            f"- Kompletność source-only: `{item['source_only_completeness']}`; ryzyko praw do obrazów: `{item['image_rights_risk']}`",
            f"- Braki: {item['missing_or_thin_content']}",
            f"- Redundancja: {item['redundancy']}",
            f"- Zalecana forma: {', '.join(item['recommended_content_form'])}",
            "",
        ])
    (destination / "content_blueprint.md").write_text("\n".join(markdown), encoding="utf-8")
    source_lines = ["# Source map", "", "Mapa zachowuje pochodzenie: slajd → przyszła jednostka wiedzy.", ""]
    for record in source_map:
        if record["status"] == "used":
            source_lines.append(f"- Slajd {record['slide_number']:03} → {', '.join(record['future_knowledge_units'])}")
        else:
            source_lines.append(f"- Slajd {record['slide_number']:03} → niewykorzystywany (`{record['unused_reason']}`)")
    (destination / "source_map.md").write_text("\n".join(source_lines) + "\n", encoding="utf-8")


def main() -> int:
    root = WORKING_ROOT / PRESENTATION
    required = [root / "slides.json", root / "triage" / "triage.json", root / "triage" / "triage_summary.md", root / "rendered_slides"]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit("Brak wymaganych danych wejściowych: " + ", ".join(missing))
    write_outputs(root / "content_blueprint")
    print(f"Utworzono blueprint: {len(PAGES)} jednostek; source map: 148 slajdów.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
