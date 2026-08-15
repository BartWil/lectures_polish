# Standard produkcji treści dydaktycznych

Ten dokument jest trwałym standardem pracy nad każdą nową jednostką dydaktyczną w repozytorium. Opisuje drogę od lokalnego pliku źródłowego do opublikowanego rozdziału Quarto. Jego wzorcową implementacją techniczną jest [pierwszy moduł produkcyjny](content/pfk/ortopedia-traumatologia/zlamania-mechanizmy-klasyfikacja.qmd); nie wolno jednak kopiować z niego treści klinicznej do kolejnych jednostek.

## Zasady niezmienne

- Prezentacja PowerPoint jest **surowym źródłem**, a nie projektem przyszłej strony. Slajd jest jednostką źródłową; strona `.qmd` jest jednostką wiedzy.
- Zachowuj pełny łańcuch pochodzenia: `prezentacja → slajd → source-only claim → evidence audit → final claim`.
- Oddzielaj źródło slajdowe od źródeł naukowych. W roboczym QMD zachowuj komentarze `<!-- source: slides ... -->`, a przy twierdzeniach po audycie `<!-- evidence: CLAIM-ID -->`.
- Docelowy rozdział ma zwykle odpowiadać 5–15 minutom czytania. Nie twórz strony dla każdego slajdu ani jednej wielkiej strony dla całego wykładu.
- Publikuj wyłącznie treść, ryciny i cytowania, które przeszły wymagany audyt. Interesująca informacja nie jest sama w sobie podstawą publikacji.

## Standardowy pipeline

### 1. Lokalne przyjęcie źródeł

- **Cel:** bezpiecznie przyjąć plik prowadzącego i ustalić jego pochodzenie.
- **Wejście:** lokalny `.pptx` lub `.docx` w `sources_local/`.
- **Wynik:** plik umieszczony w katalogu przedmiotu, np. `sources_local/pptx/pfk/ortopedia-traumatologia/`.
- **Wymagane pliki/narzędzia:** `.gitignore`, `sources_local/`.
- **Kryterium wyjścia:** znana nazwa, lokalizacja i właściciel pliku; `git status` nie pokazuje źródła.
- **Nie rób:** nie commituj źródła, nie linkuj go na stronie, nie przenoś go automatycznie do `assets/images/`.

### 2. Strukturalna ekstrakcja PPTX

- **Cel:** odzyskać dane bez interpretacji klinicznej i bez łączenia pochodzenia slajdów.
- **Wejście:** lokalny plik `.pptx`.
- **Wynik:** `imports_working/<nazwa-prezentacji>/slides.json`, `slides.md`, `images/` i raport diagnostyczny.
- **Wymagane pliki/narzędzia:** `scripts/extract_pptx.py`.
- **Kryterium wyjścia:** każdy odzyskany element wskazuje prezentację, numer slajdu i — jeśli możliwe — element slajdu.
- **Nie rób:** nie stosuj OCR bez osobnej decyzji, nie poprawiaj merytorycznie ekstrakcji, nie publikuj obrazów wyodrębnionych z PPTX.

### 3. Natywne renderowanie PowerPointa

- **Cel:** utworzyć równoległą reprezentację wizualną każdego slajdu.
- **Wejście:** ten sam lokalny PPTX.
- **Wynik:** robocze PNG slajdów w `imports_working/<nazwa-prezentacji>/rendered_slides/`.
- **Wymagane pliki/narzędzia:** `scripts/render_pptx.py` i lokalny mechanizm renderowania PowerPointa.
- **Kryterium wyjścia:** liczba wyrenderowanych obrazów odpowiada liczbie slajdów, a losowo sprawdzone pliki są czytelne.
- **Nie rób:** nie traktuj PNG jako materiału publikacyjnego ani substytutu danych strukturalnych.

### 4. Visual triage

- **Cel:** rozpoznać zależność dydaktyczną od tekstu i obrazu oraz ryzyka prawne i wrażliwe dane.
- **Wejście:** `slides.json`, renderowane PNG i raport ekstrakcji.
- **Wynik:** klasyfikacja slajdów, lista wymagających ręcznej kontroli oraz wykryte duplikaty zasobów.
- **Wymagane pliki/narzędzia:** `scripts/triage_pptx.py`.
- **Kryterium wyjścia:** dla każdego slajdu znane są co najmniej: zależność tekstowa/wizualna, rola grafiki i potrzeba ręcznego przeglądu.
- **Nie rób:** nie uznawaj automatycznej oceny za ocenę praw autorskich, nie publikuj obrazów pacjentów ani obrazów o niejasnej proweniencji.

### 5. Blueprint treści

- **Cel:** zaprojektować mały, logiczny moduł oparty na zagadnieniu, a nie kolejności slajdów.
- **Wejście:** triage, `slides.json`, robocze PNG i decyzje dydaktyczne.
- **Wynik:** blueprint z zakresem, celami, kolejnością sekcji, przypisaniem slajdów oraz listą luk.
- **Wymagane pliki/narzędzia:** `scripts/create_content_blueprint.py`, `imports_working/<nazwa-prezentacji>/`.
- **Kryterium wyjścia:** zakres jest ograniczony, a każda planowana sekcja ma wskazane źródło slajdowe lub świadomie opisaną lukę.
- **Nie rób:** nie kopiuj struktury prezentacji 1:1, nie rozszerzaj tematu poza zatwierdzony zakres.

### 6. Source-only draft

- **Cel:** utworzyć roboczy QMD wyłącznie z materiału źródłowego i zachować provenance.
- **Wejście:** zatwierdzony blueprint i dane ze slajdów.
- **Wynik:** lokalny, niepublikowany draft QMD z komentarzami `<!-- source: slides ... -->`.
- **Wymagane pliki/narzędzia:** QMD w docelowym katalogu `content/` lub równoważny plik roboczy.
- **Kryterium wyjścia:** każde twierdzenie źródłowe można prześledzić do slajdu; luki są oznaczone `CONTENT GAP`.
- **Nie rób:** nie uzupełniaj faktów wiedzą AI, nie dodawaj EBM bez audytu, nie usuwaj informacji o slajdzie.

### 7. Audyt zakresu

- **Cel:** sprawdzić, czy draft realizuje blueprint bez nadmiaru i bez ukrytych nowych twierdzeń.
- **Wejście:** source-only draft i blueprint.
- **Wynik:** decyzja „w zakresie / do korekty” oraz lista zmian redakcyjnych.
- **Wymagane pliki/narzędzia:** QMD, blueprint i ręczny przegląd.
- **Kryterium wyjścia:** zakres, struktura, cele i pytania kontrolne są spójne; wszystkie `CONTENT GAP` mają decyzję.
- **Nie rób:** nie zamieniaj audytu zakresu w audyt dowodów ani nie publikuj przed jego ukończeniem.

### 8. Audyt dowodów na poziomie claims

- **Cel:** ocenić każde istotne twierdzenie niezależnie od tego, że występowało na slajdzie.
- **Wejście:** source-only claims, wymagane źródła naukowe i klasyfikacje.
- **Wynik:** evidence audit z identyfikatorami claimów, statusem, źródłami i zalecaną redakcją.
- **Wymagane pliki/narzędzia:** `scripts/create_evidence_audit.py`, `references.bib`, dokumentacja audytu w `imports_working/`.
- **Kryterium wyjścia:** każdy claim ma jeden ze statusów: `verified`, `verified_but_needs_nuance`, `incomplete`, `outdated_or_incorrect`, `unsupported` lub `not_yet_checked`.
- **Nie rób:** nie uznawaj slajdu za dowód, nie używaj przypadkowych stron edukacyjnych ani komercyjnych do twierdzeń klinicznych.

### 9. Upgrade EBM

- **Cel:** przekształcić wyłącznie zweryfikowane claims w czytelny materiał dla studenta.
- **Wejście:** ukończony evidence audit i source-only draft.
- **Wynik:** kandydat na finalny QMD z poprawnymi cytowaniami oraz komentarzami `<!-- evidence: CLAIM-ID -->`.
- **Wymagane pliki/narzędzia:** QMD, `references.bib`, Quarto.
- **Kryterium wyjścia:** nie ma `CONTENT GAP`, `NEW EBM CLAIM REQUIRES AUDIT`, placeholderów ani claimów o statusie innym niż dopuszczony do publikacji.
- **Nie rób:** nie ukrywaj niepewności, nie wzmacniaj języka ponad dowody, nie myl klasyfikacji z zaleceniem terapeutycznym.

### 10. Autorskie ryciny

- **Cel:** zastąpić potrzebne ilustracje własnymi, bezpiecznymi i dostępnymi schematami.
- **Wejście:** potrzeba dydaktyczna, finalny QMD i zaakceptowane dowody.
- **Wynik:** specyfikacje w `imports_working/<nazwa-prezentacji>/figure_specs/`, a po akceptacji finalne SVG w `assets/images/<przedmiot>/`.
- **Wymagane pliki/narzędzia:** SVG, `assets/images/atrybucje.yml`, natywna składnia Quarto.
- **Kryterium wyjścia:** rycina ma spójny styl, podpis, tekst `alt`, opis dydaktyczny i wpis atrybucji; jest czytelna w wąskim viewport.
- **Nie rób:** nie kopiuj ani nie odrysowuj rycin bez uprawnień, nie używaj obrazu z prezentacji tylko dlatego, że był w PPTX, nie opieraj znaczenia wyłącznie na kolorze.

### 11. Final QA

- **Cel:** potwierdzić gotowość merytoryczną, techniczną i dydaktyczną przed publikacją.
- **Wejście:** finalny QMD, BibTeX, ryciny i wynik renderu.
- **Wynik:** udokumentowana decyzja „publikować / wrócić do etapu”.
- **Wymagane pliki/narzędzia:** `quarto render --clean`, QMD, `references.bib`, `atrybucje.yml`.
- **Kryterium wyjścia:** cała lista kontrolna „Final QA” poniżej jest spełniona i render kończy się sukcesem.
- **Nie rób:** nie pomijaj renderu, nie akceptuj ostrzeżeń projektowych bez wyjaśnienia, nie traktuj kontroli lokalnej jako publikacji.

### 12. Bezpieczeństwo Git

- **Cel:** do commita trafiają tylko produkcyjne pliki źródłowe.
- **Wejście:** wynik QA i `git status`.
- **Wynik:** precyzyjna lista plików do commita.
- **Wymagane pliki/narzędzia:** `.gitignore`, `git status`, `git diff --check`.
- **Kryterium wyjścia:** nie są śledzone `sources_local/`, `imports_working/`, surowe PPTX, robocze PNG, `_site/` ani `.Rhistory`.
- **Nie rób:** nie używaj szerokiego `git add .` bez sprawdzenia statusu, nie commituj roboczych artefaktów.

### 13. Integracja nawigacji

- **Cel:** dodać zaakceptowany moduł w istniejącej hierarchii strony.
- **Wejście:** moduł, który przeszedł QA.
- **Wynik:** pojedynczy wpis w odpowiedniej sekcji `_quarto.yml`.
- **Wymagane pliki/narzędzia:** `_quarto.yml`, Quarto.
- **Kryterium wyjścia:** moduł jest dostępny z właściwej sekcji przedmiotu, bez przebudowy architektury całej strony.
- **Nie rób:** nie dodawaj draftów do nawigacji, nie zmieniaj struktury strony wyłącznie dla jednej jednostki.

### 14. Publikacja

- **Cel:** bezpiecznie przekazać zatwierdzone źródła do GitHub Pages.
- **Wejście:** commit produkcyjnych plików na `main`.
- **Wynik:** push do `origin/main` i uruchomiony workflow.
- **Wymagane pliki/narzędzia:** `.github/workflows/publish.yml`, GitHub Actions, GitHub Pages.
- **Kryterium wyjścia:** commit został wypchnięty, a workflow zakończył się sukcesem.
- **Nie rób:** nie publikuj przy błędzie renderu lub nieczystym statusie Git, nie pushuj lokalnych źródeł.

### 15. Weryfikacja po publikacji

- **Cel:** sprawdzić rzeczywisty build dostępny dla odbiorcy.
- **Wejście:** udany GitHub Actions i publiczny URL.
- **Wynik:** potwierdzenie HTTP 200 oraz kontrola strony na desktopie i wąskim viewport.
- **Wymagane pliki/narzędzia:** publiczna strona GitHub Pages, przeglądarka lub kontrola HTTP.
- **Kryterium wyjścia:** działają tytuł, nawigacja, cytowania, bibliografia, SVG i linki; nie ma odwołań do katalogów lokalnych.
- **Nie rób:** nie uznawaj sukcesu workflow za pełną kontrolę UX, nie poprawiaj wygenerowanego `_site/` ręcznie.

## Źródła i evidence audit

Reguła brzmi: **claim → evidence audit → publikacja**. Preferowana hierarchia źródeł dla twierdzeń klinicznych to:

1. aktualne wytyczne, konsensusy i formalne klasyfikacje;
2. oficjalne źródła organizacji;
3. publikacje oryginalne dla klasyfikacji i definicji;
4. przeglądy systematyczne oraz metaanalizy;
5. inne badania pierwotne, gdy są potrzebne.

Każdy claim zachowuje status audytu. Claim `incomplete`, `outdated_or_incorrect`, `unsupported` lub `not_yet_checked` nie może przejść do publikacji bez jawnej zmiany, usunięcia albo nowego audytu. W `references.bib` pozostają tylko rzeczywiście potrzebne pozycje, a każda publikowana pozycja musi być cytowana przez QMD.

## Bezpieczeństwo źródeł i obrazów

- `sources_local/` nigdy nie trafia do commita.
- `imports_working/` nigdy nie trafia do commita ani na stronę.
- Wyekstrahowane obrazy i renderowane slajdy nie są publikowane automatycznie.
- Do `assets/images/` trafiają wyłącznie zaakceptowane zasoby, z wpisem w `assets/images/atrybucje.yml`.
- Obrazy pacjentów lub potencjalnie wrażliwe materiały wymagają osobnego audytu dopuszczalności publikacji.
- Samo użycie obrazu w PPTX nie daje prawa do jego dalszej publikacji.

## Lista kontrolna: Final QA

### Treść

- [ ] Moduł realizuje zatwierdzony blueprint, a nie kolejność slajdów.
- [ ] Nie ma `CONTENT GAP`, placeholderów ani niezaudytowanych nowych twierdzeń.
- [ ] Terminologia i rozróżnienia pojęć są konsekwentne.
- [ ] Cele, podsumowanie i pytania kontrolne wynikają z treści.

### Dowody

- [ ] Każdy istotny claim ma wynik evidence audit i komentarz `<!-- evidence: CLAIM-ID -->`.
- [ ] Cytowania są poprawne, a `references.bib` nie ma duplikatów ani nieużywanych pozycji dodanych dla modułu.
- [ ] DOI, URL i metadane zostały technicznie sprawdzone na tyle, na ile jest to możliwe.

### Ryciny

- [ ] Każda rycina ma podpis, `alt`, opis dydaktyczny i wpis w `assets/images/atrybucje.yml`.
- [ ] Ryciny nie kopiują ani nie odrysowują zasobów bez uprawnień.
- [ ] Etykiety są czytelne na desktopie i w wąskim viewport, również bez rozróżniania samym kolorem.

### Technika i dostępność

- [ ] Struktura nagłówków, tabele, callouty, linki i bibliografia są poprawne.
- [ ] Nie ma poziomego scrolla na telefonie.
- [ ] `quarto render --clean` kończy się sukcesem.

### Publikacja

- [ ] `git status` nie zawiera lokalnych źródeł ani artefaktów roboczych.
- [ ] Moduł jest dodany do właściwej sekcji `_quarto.yml`.
- [ ] Workflow GitHub Actions zakończył się sukcesem.
- [ ] Publiczna strona odpowiada HTTP 200 i została skontrolowana po publikacji.

## Gdy standardowy pipeline nie wystarcza

SmartArt, grupowane elementy, złożone wykresy, nietypowe tabele, osadzone media, tekst w obrazach, obrazy diagnostyczne i slajdy zależne przede wszystkim od grafiki mogą wymagać dodatkowej walidacji wizualnej lub analizy XML. Takie odstępstwo dokumentuj przy danej prezentacji: co nie zadziałało, jaka metoda dodatkowa została użyta i jakie pozostają ograniczenia. Pojedynczy wyjątek nie zmienia standardu globalnego.

## Zasada operacyjna

Przed rozpoczęciem nowego modułu przeczytaj ten dokument i stosuj wszystkie etapy odpowiednie dla jego źródeł. Odstępstwa wymagają wyraźnego uzasadnienia w materiale roboczym lub w opisie zmiany.
