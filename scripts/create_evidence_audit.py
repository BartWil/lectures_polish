"""Tworzy lokalny audyt EBM dla pilotażowego rozdziału o złamaniach.

Skrypt nie modyfikuje plików Quarto. Utrzymuje rozdzielnie pochodzenie
prezentacyjne (source_slides) i źródła weryfikacji naukowej
(evidence_sources).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRESENTATION = "WYKŁAD_1_2_Podstawy_traumatologia_Złamania_Skręcenia"
OUTPUT = ROOT / "imports_working" / PRESENTATION / "evidence_audit"
CHECKED_AT = "2026-08-11"

SOURCES = [
    {
        "source_id": "EBM-001",
        "title": "Fractures, Bone — MeSH",
        "organization": "U.S. National Library of Medicine",
        "year": "2026 (rekord MeSH bieżący w dniu kontroli)",
        "evidence_type": "kontrolowane słownictwo biomedyczne",
        "url": "https://www.ncbi.nlm.nih.gov/mesh/68050723",
        "relevant_locator": "Definicja: ‘Breaks in bones.’",
    },
    {
        "source_id": "EBM-002",
        "title": "AO Surgery Reference: Extraarticular fracture, simple",
        "organization": "AO Foundation",
        "year": "strona bieżąca, sprawdzona 2026-08-11",
        "evidence_type": "oficjalne źródło organizacji naukowej",
        "url": "https://surgeryreference.aofoundation.org/orthopedic-trauma/adult-trauma/distal-femur/extraarticular-fracture-simple/definition",
        "relevant_locator": "General considerations; podtypy spiralny, skośny i poprzeczny oraz przykład związku sił skrętnych z morfologią.",
    },
    {
        "source_id": "EBM-003",
        "title": "AO Surgery Reference: Principles of management of open fractures",
        "organization": "AO Foundation",
        "year": "strona bieżąca, sprawdzona 2026-08-11",
        "evidence_type": "oficjalne źródło organizacji naukowej",
        "url": "https://surgeryreference.aofoundation.org/orthopedic-trauma/adult-trauma/further-reading/principles-of-management-of-open-fractures",
        "relevant_locator": "Classification of open fractures; wound-severity classification; opis Gustilo–Mendoza–Williams i IIIC.",
    },
    {
        "source_id": "EBM-004",
        "title": "Fracture and Dislocation Classification Compendium—2018",
        "organization": "Orthopaedic Trauma Association i AO Foundation",
        "year": "2018",
        "evidence_type": "oficjalny compendium klasyfikacji",
        "url": "https://ota.org/media/531625/rev-jotv32n1s-issue-softproof_11218.pdf",
        "relevant_locator": "s. S106, OTA Open Fracture Classification; całość compendium dla terminologii AO/OTA.",
    },
    {
        "source_id": "EBM-005",
        "title": "Prevention of infection in the treatment of one thousand and twenty-five open fractures of long bones: retrospective and prospective analyses",
        "organization": "Gustilo i Anderson; PubMed",
        "year": "1976",
        "evidence_type": "publikacja pierwotna klasyfikacji stopni I–III",
        "url": "https://pubmed.ncbi.nlm.nih.gov/773941/",
        "relevant_locator": "Streszczenie oraz dane bibliograficzne; J Bone Joint Surg Am 58(4):453–458; DOI 10.2106/00004623-197658040-00004.",
    },
    {
        "source_id": "EBM-006",
        "title": "Problems in the management of type III (severe) open fractures: a new classification of type III open fractures",
        "organization": "Gustilo, Mendoza i Williams; PubMed",
        "year": "1984",
        "evidence_type": "publikacja pierwotna klasyfikacji typu III",
        "url": "https://pubmed.ncbi.nlm.nih.gov/6471139/",
        "relevant_locator": "Streszczenie oraz dane bibliograficzne; J Trauma 24(8):742–746; DOI 10.1097/00005373-198408000-00009.",
    },
    {
        "source_id": "EBM-007",
        "title": "NICE NG37: Fractures (complex): assessment and management",
        "organization": "National Institute for Health and Care Excellence",
        "year": "aktualizacja 2022; sprawdzone 2026-08-11",
        "evidence_type": "aktualna wytyczna",
        "url": "https://www.nice.org.uk/guidance/ng37/chapter/recommendations",
        "relevant_locator": "Open fractures; rekomendacje 1.2.20–1.2.30, użycie określeń Gustilo–Anderson IIIA/IIIB w kontekście postępowania.",
    },
]

CLAIMS = [
    {
        "claim_id": "FMC-001",
        "claim_text": "Złamanie jest zaburzeniem ciągłości struktury kości.",
        "qmd_section": "Wprowadzenie",
        "source_slides": [33],
        "citation_required": "yes",
        "clinical_importance": "medium",
        "evidence_status": "verified",
        "recommended_action": "Zachować sens definicji; w wersji EBM dodać źródło definicyjne.",
        "evidence_sources": ["EBM-001"],
        "notes": "Definicja jest zgodna z MeSH. W tekście klinicznym można później doprecyzować, że uraz obejmuje również tkanki otaczające, jeśli będzie to potrzebne dla celu rozdziału.",
    },
    {
        "claim_id": "FMC-002",
        "claim_text": "Określenia zamknięte, otwarte, zmęczeniowe, patologiczne, osteoporotyczne, okołoprotezowe i typu zielonej gałązki odnoszą się do różnych osi opisu złamania, a nie do jednego wspólnego kryterium.",
        "qmd_section": "Czym jest złamanie",
        "source_slides": [33, 48],
        "citation_required": "yes",
        "clinical_importance": "medium",
        "evidence_status": "verified_but_needs_nuance",
        "recommended_action": "Zachować rozróżnienie osi opisu, ale rozdzielić w wersji EBM klasyfikację urazu, etiologię/insuficjencję oraz szczególne sytuacje kliniczne; nie przedstawiać tej listy jako jednego systemu klasyfikacyjnego.",
        "evidence_sources": ["EBM-001", "EBM-004"],
        "notes": "Compendium AO/OTA jest systemem klasyfikacji morfologiczno-anatomicznej; nie zastępuje wszystkich opisów klinicznych wymienionych w slajdzie.",
    },
    {
        "claim_id": "FMC-003",
        "claim_text": "Złamanie może być następstwem urazu bezpośredniego lub pośredniego, urazu niskoenergetycznego albo choroby kości; prezentacja używa też skrótu ‘bez urazu’.",
        "qmd_section": "Jak dochodzi do złamania",
        "source_slides": [36],
        "citation_required": "yes",
        "clinical_importance": "high",
        "evidence_status": "verified_but_needs_nuance",
        "recommended_action": "Zachować podział mechanizmów, lecz zastąpić potencjalnie mylące ‘bez urazu’ sformułowaniem o złamaniu po niewielkim obciążeniu lub bez rozpoznawalnego urazu w kontekście osłabionej/zmienionej chorobowo kości.",
        "evidence_sources": ["EBM-001", "EBM-002"],
        "notes": "Wymaga później osobnego źródła dla rozróżnienia złamań patologicznych, niewydolnościowych i osteoporotycznych, jeśli rozdział ma definiować te terminy.",
    },
    {
        "claim_id": "FMC-004",
        "claim_text": "Sumujące się mikrourazy mogą prowadzić do złamania zmęczeniowego.",
        "qmd_section": "Jak dochodzi do złamania",
        "source_slides": [36],
        "citation_required": "yes",
        "clinical_importance": "medium",
        "evidence_status": "verified",
        "recommended_action": "Pozostawić; dodać źródło specyficzne dla złamań zmęczeniowych dopiero, jeśli temat zostanie rozwinięty ponad wzmiankę definicyjną.",
        "evidence_sources": ["EBM-001"],
        "notes": "MeSH rozróżnia stress fractures jako odrębną kategorię; aktualny tekst nie podaje niezweryfikowanych progów ani zaleceń klinicznych.",
    },
    {
        "claim_id": "FMC-005",
        "claim_text": "Nadmierne obciążenie kości może obejmować kompresję, dystrakcję, ścinanie i rotację; działania te mogą występować łącznie.",
        "qmd_section": "Mechanizm urazu a charakter złamania",
        "source_slides": [38],
        "citation_required": "yes",
        "clinical_importance": "high",
        "evidence_status": "verified",
        "recommended_action": "Pozostawić jako wprowadzenie; w wersji EBM powiązać je ostrożnie z morfologią, bez sugerowania deterministycznej relacji jeden mechanizm–jeden typ złamania.",
        "evidence_sources": ["EBM-002"],
        "notes": "AO podaje przykłady, w których złamania spiralne i skośne wiążą się z siłami skrętnymi; jest to przykład zależny od okolicy anatomicznej, a nie uniwersalna reguła.",
    },
    {
        "claim_id": "FMC-006",
        "claim_text": "Złamania można opisywać przez stan tkanek miękkich, charakter powstania, przebieg szczeliny, przemieszczenie oraz lokalizację; kategorie te mogą współistnieć.",
        "qmd_section": "Podstawowe sposoby klasyfikacji złamań",
        "source_slides": [33, 48, 49],
        "citation_required": "yes",
        "clinical_importance": "high",
        "evidence_status": "verified_but_needs_nuance",
        "recommended_action": "Pozostawić jako dydaktyczny opis cech, ale jasno oddzielić go od formalnej klasyfikacji AO/OTA i doprecyzować, że ‘ostre/przewlekłe’ nie jest osią standardowego kodu AO/OTA.",
        "evidence_sources": ["EBM-004"],
        "notes": "Formalne systemy klasyfikacyjne nie pokrywają w pojedynczej tabeli wszystkich klinicznych cech z prezentacji.",
    },
    {
        "claim_id": "FMC-007",
        "claim_text": "Do podstawowych opisów morfologii szczeliny należą określenia: poprzeczna, skośna, spiralna i wieloodłamowa.",
        "qmd_section": "Morfologia i przebieg szczeliny złamania",
        "source_slides": [48],
        "citation_required": "yes",
        "clinical_importance": "medium",
        "evidence_status": "verified",
        "recommended_action": "Pozostawić terminologię; przy ilustracji użyć autorskiego schematu z osobną kontrolą merytoryczną, bez kopiowania rycin ze slajdów.",
        "evidence_sources": ["EBM-001", "EBM-002", "EBM-004"],
        "notes": "AO stosuje terminy transverse, oblique i spiral dla prostych złamań; ‘wieloodłamowe’ opisuje liczbę odłamów, więc nie jest tym samym wymiarem co orientacja szczeliny.",
    },
    {
        "claim_id": "FMC-008",
        "claim_text": "Opis przemieszczenia może obejmować skrócenie lub wklinowanie, wydłużenie albo rozejście odłamów, zagięcie osiowe i rotację.",
        "qmd_section": "Przemieszczenie odłamów",
        "source_slides": [48],
        "citation_required": "yes",
        "clinical_importance": "high",
        "evidence_status": "verified_but_needs_nuance",
        "recommended_action": "Ujednolicić później polską nomenklaturę i rozdzielić translację, skrócenie/distrakcję, angulację oraz rotację; nie utożsamiać wklinowania z każdą postacią skrócenia.",
        "evidence_sources": ["EBM-002", "EBM-004"],
        "notes": "Wymaga ręcznej redakcji terminologicznej przed publikacją EBM; w tym audycie nie znaleziono podstaw do uznania listy za błędną.",
    },
    {
        "claim_id": "FMC-009",
        "claim_text": "Złamanie otwarte wiąże się z naruszeniem ciągłości skóry i tkanek miękkich, a złamanie zamknięte takiego połączenia rany ze złamaniem nie ma.",
        "qmd_section": "Złamania zamknięte i otwarte",
        "source_slides": [33, 48, 50],
        "citation_required": "yes",
        "clinical_importance": "high",
        "evidence_status": "verified_but_needs_nuance",
        "recommended_action": "Doprecyzować w wersji EBM, że rozpoznanie złamania otwartego dotyczy komunikacji rany ze złamaniem; nie wymaga widocznego wystawania kości i w praktyce wymaga ostrożnej oceny klinicznej.",
        "evidence_sources": ["EBM-003", "EBM-006"],
        "notes": "Obecne zdanie jest dydaktycznie skrótowe. NICE prowadzi osobny tor postępowania dla open fractures, a AO podkreśla znaczenie oceny tkanek miękkich.",
    },
    {
        "claim_id": "FMC-010",
        "claim_text": "Klasyfikacja Gustilo–Andersona opisuje stopnie I, II oraz IIIA, IIIB i IIIC przez ciężkość rany i uszkodzeń tkanek miękkich; IIIC obejmuje uraz tętniczy wymagający naprawy dla zachowania żywotności kończyny.",
        "qmd_section": "Złamania zamknięte i otwarte",
        "source_slides": [50],
        "citation_required": "yes",
        "clinical_importance": "high",
        "evidence_status": "verified_but_needs_nuance",
        "recommended_action": "Zachować nazwę i główną ideę, lecz oprzeć przyszły opis na publikacji 1976 dla I–III i publikacji 1984 dla podziału typu III; dodać zastrzeżenie, że pełniejsza ocena tkanek miękkich może następować po opracowaniu rany.",
        "evidence_sources": ["EBM-003", "EBM-005", "EBM-006", "EBM-007"],
        "notes": "Publikacja z 1976 r. stanowi źródło stopni I–III, a publikacja z 1984 r. — późniejszego podziału typu III. AO wskazuje, że Gustilo–Anderson jest powszechnie używany, ale istnieją bardziej szczegółowe systemy AO/OTA; nie wolno na jego podstawie samodzielnie budować algorytmu leczenia w tym rozdziale.",
    },
]

CONTENT_GAPS = [
    {
        "gap_id": "GAP-001",
        "title": "Relacja sił z morfologią złamania",
        "source_slides": [34, 35, 38, 39],
        "status": "incomplete",
        "assessment": "Prezentacja wymienia siły, ale nie daje wystarczającego tekstowego uzasadnienia dla pełnego mapowania siła → morfologia. Ryciny źródłowe nie są gotowe do publikacji ani nie mogą zastąpić weryfikowalnego opisu.",
        "recommended_sources": ["EBM-002", "EBM-004"],
        "future_decision": "Przygotować autorski, ostrożnie sformułowany schemat z przykładami zależnymi od okolicy; nie przedstawiać relacji jako bezwzględnej.",
    },
    {
        "gap_id": "GAP-002",
        "title": "Niekompletny opis zastosowania Gustilo–Anderson",
        "source_slides": [50, 51],
        "status": "incomplete",
        "assessment": "W QMD jest jedynie zarys stopni. Brakuje bezpiecznego, samodzielnego wyjaśnienia zakresu klasyfikacji, momentu wiarygodnej oceny oraz rozdzielenia klasyfikacji od decyzji terapeutycznych.",
        "recommended_sources": ["EBM-003", "EBM-005", "EBM-006", "EBM-007", "EBM-004"],
        "future_decision": "Uzupełnić po osobnej decyzji o zakresie rozdziału; wątek postępowania klinicznego pozostawić w osobnym module i oprzeć go na aktualnych wytycznych.",
    },
]


def write_markdown() -> str:
    lines = [
        "# Audyt EBM — złamania: mechanizmy i klasyfikacja",
        "",
        f"- Data kontroli: {CHECKED_AT}",
        "- Zakres: claim-level audit pilotażowego QMD; bez modyfikacji tekstu dydaktycznego.",
        f"- Materiał źródłowy: `{PRESENTATION}`.",
        "- Rozdzielenie provenance: `source_slides` wskazuje wyłącznie slajdy prezentacji, a `evidence_sources` wyłącznie źródła zewnętrzne użyte do weryfikacji.",
        "",
        "## Metoda i ograniczenia",
        "",
        "Zweryfikowano twierdzenia merytoryczne obecne w QMD. Nie oceniano pytań kontrolnych, nagłówków, komentarzy technicznych ani przyszłych rycin. Audyt nie jest poradą kliniczną ani algorytmem postępowania. Status `verified_but_needs_nuance` oznacza, że sens twierdzenia jest zgodny ze źródłami, ale publikowana wersja wymaga doprecyzowania zakresu, terminologii lub ograniczeń.",
        "",
        "## Wynik zbiorczy",
        "",
        "| Status | Liczba |",
        "|---|---:|",
        "| verified | 4 |",
        "| verified_but_needs_nuance | 6 |",
        "| incomplete | 0 |",
        "| outdated_or_incorrect | 0 |",
        "| unsupported | 0 |",
        "| not_yet_checked | 0 |",
        "",
        "Dwie oznaczone w QMD luki treści są raportowane osobno poniżej; nie są liczone jako istniejące twierdzenia.",
        "",
        "## Audyt twierdzeń",
        "",
        "| ID | Sekcja | Slajdy źródłowe | Status | Decyzja |",
        "|---|---|---|---|---|",
    ]
    for claim in CLAIMS:
        lines.append(
            f"| {claim['claim_id']} | {claim['qmd_section']} | {', '.join(map(str, claim['source_slides']))} | `{claim['evidence_status']}` | {claim['recommended_action']} |"
        )
    lines.extend(["", "## Szczegóły twierdzeń", ""])
    for claim in CLAIMS:
        lines.extend([
            f"### {claim['claim_id']}",
            "",
            f"- Twierdzenie: {claim['claim_text']}",
            f"- Sekcja QMD: {claim['qmd_section']}",
            f"- Slajdy źródłowe: {', '.join(map(str, claim['source_slides']))}",
            f"- Cytowanie wymagane: {claim['citation_required']}",
            f"- Znaczenie kliniczne: {claim['clinical_importance']}",
            f"- Status: `{claim['evidence_status']}`",
            f"- Zalecane działanie: {claim['recommended_action']}",
            f"- Źródła weryfikujące: {', '.join(claim['evidence_sources'])}",
            f"- Uwagi: {claim['notes']}",
            "",
        ])
    lines.extend(["## Luki treści oznaczone w QMD", ""])
    for gap in CONTENT_GAPS:
        lines.extend([
            f"### {gap['gap_id']} — {gap['title']}",
            "",
            f"- Slajdy źródłowe: {', '.join(map(str, gap['source_slides']))}",
            f"- Ocena: `{gap['status']}`",
            f"- Ustalenie: {gap['assessment']}",
            f"- Źródła do późniejszego uzupełnienia: {', '.join(gap['recommended_sources'])}",
            f"- Decyzja na kolejny etap: {gap['future_decision']}",
            "",
        ])
    lines.extend(["## Katalog źródeł", ""])
    for source in SOURCES:
        lines.extend([
            f"### {source['source_id']} — {source['title']}",
            "",
            f"- Organizacja / autor: {source['organization']}",
            f"- Rok / wersja: {source['year']}",
            f"- Typ: {source['evidence_type']}",
            f"- Adres: {source['url']}",
            f"- Lokalizator: {source['relevant_locator']}",
            "",
        ])
    lines.extend([
        "## Decyzja przed wersją EBM",
        "",
        "Można przejść do przygotowania wersji EBM, ale najpierw należy rozstrzygnąć dwie luki treści, ujednolicić terminologię przemieszczenia oraz wyraźnie oddzielić opis klasyfikacji Gustilo–Andersona od postępowania klinicznego. Żadna zmiana QMD nie została wykonana w tym etapie.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    payload = {
        "audit_metadata": {
            "audit_date": CHECKED_AT,
            "qmd": "content/pfk/ortopedia-traumatologia/zlamania-mechanizmy-klasyfikacja.qmd",
            "presentation": PRESENTATION,
            "scope": "audyt claim-by-claim; bez modyfikacji QMD",
            "allowed_statuses": [
                "verified",
                "verified_but_needs_nuance",
                "incomplete",
                "outdated_or_incorrect",
                "unsupported",
                "not_yet_checked",
            ],
        },
        "evidence_catalog": SOURCES,
        "claims": CLAIMS,
        "content_gaps": CONTENT_GAPS,
    }
    (OUTPUT / "claims.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    fields = [
        "claim_id", "claim_text", "qmd_section", "source_slides", "citation_required",
        "clinical_importance", "evidence_status", "recommended_action", "evidence_sources", "notes",
    ]
    with (OUTPUT / "claims.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for claim in CLAIMS:
            row = claim.copy()
            row["source_slides"] = ";".join(map(str, claim["source_slides"]))
            row["evidence_sources"] = ";".join(claim["evidence_sources"])
            writer.writerow(row)
    (OUTPUT / "evidence_audit.md").write_text(write_markdown(), encoding="utf-8")


if __name__ == "__main__":
    main()
