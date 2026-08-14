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
