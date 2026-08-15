# Skrypty pomocnicze

W przyszłości mogą tu znaleźć się narzędzia do wspomaganego importu plików `.pptx` i `.docx` przechowywanych lokalnie w `sources_local/`.

Skrypty zapisują wyniki ekstrakcji wyłącznie w `imports_working/`. Nie powinny nadpisywać istniejących materiałów `.qmd`, commitować surowych plików ani publikować tekstów czy obrazów bez ręcznej kontroli.

## Strukturalna ekstrakcja protokołów rehabilitacyjnych PDF

`extract_rehab_protocol_pdf.py` odwzorowuje tekstowy PDF jako strukturę
`dokument → strona → sekcja → element`. Nie używa OCR, nie ocenia poprawności
zaleceń i nie tworzy protokołu dla studentów.

Przykładowe uruchomienie:

```powershell
python scripts/extract_rehab_protocol_pdf.py `
  sources_local/protocols/<obszar>/<procedura>/<instytucja>/<plik>.pdf `
  imports_working/protocols/<source_id> `
  --source-id <source_id>
```

W katalogu roboczym powstają:

- `pages.json` — bloki tekstowe, tabele i hiperłącza z pozycją na stronie;
- `protocol_structure.json` — rozpoznane komponenty oraz referencje;
- `phase_map.json` — mechaniczna mapa faz i ich elementów;
- `action_inventory.json` — stabilne identyfikatory działań wymagających
  późniejszego action-level evidence audit;
- `diagnostic_report.md` — zakres i ograniczenia ekstrakcji.

Przed rozpoczęciem audytu należy ręcznie sprawdzić wielokolumnowe układy,
łamane punkty, tabele i elementy zależne od wyglądu strony. PDF oraz wszystkie
wyniki tego etapu pozostają lokalne i ignorowane przez Git.

## Normalizacja działań do planu evidence audit

`normalize_rehab_protocol_actions.py` dodaje do inventory wyłącznie warstwę
organizacyjną: rodzinę działania, priorytet, testowalność, grupę powtórzeń i
śledzalne pytania do późniejszego audytu. Nie przeszukuje literatury, nie
ocenia zaleceń źródłowego protokołu i nie tworzy własnego protokołu.

```powershell
python scripts/normalize_rehab_protocol_actions.py `
  imports_working/protocols/<source_id>/action_inventory.json `
  imports_working/protocols/<source_id> `
  --question-prefix <PREFIKS>-EQ
```

Powstają lokalne pliki:

- `action_inventory_normalized.json` — oryginalne rekordy z dodaną warstwą
  normalizacji; identyfikatory źródłowe pozostają niezmienione;
- `evidence_questions.json` — pytania grupujące działania Tier A i Tier B;
- `threshold_inventory.json` — progi z bezpośrednim wskazaniem rekordu
  źródłowego;
- `evidence_audit_template.json` — pusty schemat późniejszej oceny evidence,
  bez źródeł, wyników researchu ani decyzji klinicznych.

Przed research należy ręcznie zweryfikować wszystkie rekordy Tier A, progi,
rekordy oznaczone `requires_manual_review` i reprezentatywną próbę pozostałych
rekordów. Wyniki normalizacji pozostają w `imports_working/` i nie podlegają
publikacji.
