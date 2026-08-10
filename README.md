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

## Publikacja

Workflow `.github/workflows/publish.yml` publikuje stronę po wysłaniu zmian do gałęzi `main`. W ustawieniach repozytorium GitHub należy zezwolić GitHub Actions na zapis do repozytorium, a w GitHub Pages jako źródło wybrać gałąź `gh-pages`.
