# Stałe instrukcje dla Codex

## Cel projektu

Repozytorium zawiera polskojęzyczną bazę materiałów dydaktycznych publikowaną jako strona Quarto na GitHub Pages. Projekt ma pozostać prosty, czytelny i łatwy do ręcznej edycji.

## Język i styl

- Wszystkie treści dla odbiorców, komunikaty, komentarze i dokumentacja pisane są po polsku, chyba że nazwa własna lub składnia techniczna wymaga innego języka.
- Stosuj prosty, akademicki układ: krótkie akapity, opisowe nagłówki i minimum elementów dekoracyjnych.
- Treść dydaktyczną zapisuj przede wszystkim w `.qmd` lub Markdown, a nie w ręcznie tworzonym HTML.

## Struktura treści

- Każdy przedmiot ma własny katalog w `content/` oraz stronę `index.qmd`.
- Materiały publikowane należą do `content/`; obrazy do `assets/images/`.
- Oryginalne pliki prowadzących (`.pptx`, `.docx`) przechowuj wyłącznie w `sources/`. Nie linkuj ich automatycznie jako elementów strony.
- Skrypty pomocnicze, w tym przyszły import `.pptx` i `.docx`, umieszczaj w `scripts/`.

## Źródła i licencje

- Każdy opublikowany obraz musi mieć wpis w `assets/images/atrybucje.yml`: plik, autor lub instytucja, adres źródłowy, licencja i informacja o modyfikacji.
- Cytowania naukowe prowadź w `references.bib` i stosuj standardowy zapis Pandoc/Quarto, np. `[@klucz2026]`.
- Nie kopiuj treści ani grafik, dla których nie można ustalić uprawnień do wykorzystania.

## Publikacja i weryfikacja

- Nie edytuj wygenerowanych plików w `_site/` ani katalogu `_freeze/` ręcznie.
- Przed przekazaniem zmian uruchom `quarto render`, gdy Quarto jest dostępne, i usuń błędy renderowania.
- Utrzymuj workflow w `.github/workflows/publish.yml` zgodny z GitHub Pages.
- Nie importuj ani nie przepisuj materiałów dydaktycznych bez wyraźnego polecenia użytkownika.
