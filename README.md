# lectures_polish

Polskojęzyczna baza materiałów dydaktycznych tworzona w [Quarto](https://quarto.org/) i przeznaczona do publikacji na GitHub Pages.

## Praca lokalna

Po zainstalowaniu Quarto uruchom w głównym katalogu projektu:

```powershell
quarto preview
```

Aby zbudować pełną wersję strony:

```powershell
quarto render
```

Szczegółowe, stałe zasady pracy znajdują się w [AGENTS.md](AGENTS.md).

## Edycja w przeglądarce

Do krótkiej poprawki tekstu można użyć edytora [github.dev](https://github.dev/BartWil/lectures_polish): w widoku repozytorium na GitHub wystarczy nacisnąć klawisz `.`. Ten tryb nie udostępnia terminala ani lokalnego podglądu Quarto.

Do tworzenia i sprawdzania materiałów używaj GitHub Codespaces. Konfiguracja w
`.devcontainer/` automatycznie instaluje Quarto, Python oraz biblioteki obecnych
skryptów. Po utworzeniu Codespace:

1. otwórz plik `.qmd` i wybierz polecenie **Quarto: Preview**;
2. w razie potrzeby przełącz edytor na tryb wizualny poleceniem **Edit in Visual Mode**;
3. przed commitem uruchom `quarto render --clean`.

Codespaces nie zastępuje prywatnego miejsca dla surowych materiałów źródłowych. Pliki `.pptx`, `.docx`, robocze ekstrakcje i materiały o niejasnych prawach nadal pozostają poza tym publicznym repozytorium.

## Lokalne materiały źródłowe

Surowe prezentacje `.pptx`, dokumenty `.docx` oraz wyniki ich automatycznej ekstrakcji nie należą do publicznego repozytorium. Przechowuj je wyłącznie lokalnie:

```text
sources_local/
├── pptx/
└── docx/

imports_working/
```

Katalogi te są ignorowane przez Git. Tekst i obrazy odzyskane z prezentacji są materiałem roboczym, a nie gotową treścią strony. Do `assets/images/` można dodać wyłącznie grafikę ręcznie zatwierdzoną do publikacji, z udokumentowanym źródłem i licencją.

## Publikacja

Workflow `.github/workflows/publish.yml` publikuje stronę po wysłaniu zmian do gałęzi `main`. W ustawieniach repozytorium GitHub należy zezwolić GitHub Actions na zapis do repozytorium, a w GitHub Pages jako źródło wybrać gałąź `gh-pages`.
