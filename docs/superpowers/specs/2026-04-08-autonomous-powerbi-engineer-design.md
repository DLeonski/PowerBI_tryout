# Design: Autonomiczny Inżynier Power BI

**Data:** 2026-04-08  
**Status:** Zatwierdzony

---

## Cel projektu

Agent przyjmujący polecenie w języku naturalnym i plik CSV, który autonomicznie: profiluje dane, czyści anomalie, projektuje model danych, dobiera wizualizacje na podstawie skills i generuje gotowy plik `.pbix` wraz z raportem tekstowym.

---

## Architektura ogólna

```
Użytkownik
    │  polecenie naturalne + ścieżka do CSV
    ▼
┌─────────────────────────────┐
│        CLI (main.py)        │
└────────────┬────────────────┘
             │
    ┌────────▼─────────┐
    │   Main Agent      │  ← Claude API (tool use)
    │  (orchestrator)   │
    └────────┬──────────┘
             │ po wykonaniu pracy
    ┌────────▼──────────┐
    │  Reviewer Agent   │  ← osobna sesja Claude
    │  (self-check)     │
    └────────┬──────────┘
             │ zatwierdzone / feedback (max 2 iteracje)
    ┌────────▼──────────┐
    │    Output         │  ← .pbix + raport .md
    └───────────────────┘
```

**Model LLM:** Claude (Anthropic API) — tool use do orkiestracji kroków  
**Format wejściowy:** CSV  
**Format wyjściowy:** `.pbix` (Power BI Desktop) + raport `.md`  
**Tryb działania:** Hybrydowy — autonomiczny, zatrzymuje się przy niejednoznaczności lub po 2 nieudanych iteracjach review

---

## Struktura plików

```
powerbi_agent/
├── main.py                    # punkt wejścia CLI
├── config.py                  # klucze API, ścieżki domyślne
│
├── agent/
│   ├── main_agent.py          # główny agent Claude (tool use)
│   ├── reviewer_agent.py      # agent recenzent (osobna sesja)
│   └── tools.py               # definicje narzędzi dla agenta
│
├── data/
│   └── processor.py           # pandas: ładowanie, profilowanie, czyszczenie
│
├── pbix/
│   ├── generator.py           # rozpakowuje/modyfikuje/pakuje .pbix
│   ├── template.pbix          # bazowy szablon (plik binarny)
│   └── schemas/               # JSON schemas struktury .pbix
│
├── skills/
│   ├── base/
│   │   ├── dashboard-design.md    # zawsze ładowany
│   │   └── general-rules.md       # zawsze ładowany
│   ├── viz-routing.md             # zawsze ładowany — mapa: typ danych → typ wykresu
│   └── viz/
│       ├── line-chart.md          # ładowany gdy agent wybierze ten typ
│       ├── bar-chart.md
│       ├── kpi-card.md
│       ├── scatter-plot.md
│       ├── pie-chart.md
│       └── table.md
│
└── output/                    # generowane .pbix i raporty .md
```

---

## Narzędzia (tools) dostępne dla Main Agenta

| Tool | Opis |
|------|------|
| `profile_data(csv_path)` | Analizuje typy kolumn, rozkłady, outliers, brakujące wartości |
| `load_skills(data_profile)` | Ładuje bazowe skills + dynamicznie dobrane na podstawie profilu |
| `clean_data(rules)` | Czyści anomalie wg reguł; każda decyzja logowana do raportu |
| `design_model(spec)` | Projektuje tabele, relacje, miary DAX |
| `generate_pbix(model_spec)` | Tworzy plik .pbix przez manipulację ZIP/JSON |
| `write_report(summary)` | Zapisuje raport .md z opisem wszystkich decyzji agenta |

Każdy tool zwraca: `{"status": "ok"|"error", "data": ..., "message": ...}`

---

## System Skills (dwupoziomowy)

### Poziom 1 — Zawsze ładowane
- `skills/base/dashboard-design.md` — ogólne zasady layoutu dashboardu
- `skills/base/general-rules.md` — ogólne zasady pracy z danymi
- `skills/viz-routing.md` — mapa: typ danych → rekomendowany typ wykresu

### Poziom 2 — Ładowane dynamicznie po decyzji agenta
Agent czyta `viz-routing.md`, profil danych → decyduje które wykresy użyć → ładuje odpowiednie `skills/viz/*.md` z detalami designu każdego wykresu (kolory, osie, formatowanie, dobre praktyki).

**Przykład:**  
Dane mają kolumnę `Date` + `Revenue` → `viz-routing.md` sugeruje line chart → agent ładuje `skills/viz/line-chart.md` przed projektowaniem tej wizualizacji.

---

## Przepływ agenta (6 faz)

### Faza 1 — Rozumienie zadania
1. Wczytaj polecenie użytkownika
2. Wywołaj `profile_data(csv_path)` → profil danych
3. Wywołaj `load_skills(data_profile)` → bazowe skills + viz-routing.md

### Faza 2 — Czyszczenie danych
1. Na podstawie profilu i skills zdecyduj reguły czyszczenia (outliers, duplikaty, null-handling)
2. Wywołaj `clean_data(rules)`
3. Zaloguj każdą decyzję (co usunięto i dlaczego)

### Faza 3 — Projektowanie modelu
1. Określ typy wykresów na podstawie `viz-routing.md` i profilu danych
2. Wywołaj `load_skills(chosen_chart_types)` → ładuje `skills/viz/<chart-type>.md` dla każdego wybranego wykresu
3. Wywołaj `design_model(spec)` → tabele, relacje, miary DAX, układ dashboardu

### Faza 4 — Generowanie .pbix
1. Wywołaj `generate_pbix(model_spec)`
2. Generator rozpakowuje `template.pbix` (ZIP)
3. Modyfikuje `DataModel` JSON (schemat, dane, miary DAX)
4. Modyfikuje `Report/Layout` JSON (wizualizacje, pozycje, formatowanie)
5. Pakuje z powrotem do `.pbix`

### Faza 5 — Self-review (Reviewer Agent)
1. Osobna sesja Claude dostaje: polecenie + model_spec + log decyzji
2. Ocenia: czy wizualizacje pasują do danych, poprawność DAX, sensowność czyszczenia
3. **OK** → przejdź do Fazy 6
4. **Problem** → Main Agent dostaje feedback, iteruje (max 2 razy)
5. Po 2 nieudanych próbach → zatrzymaj i wygeneruj raport z opisem problemu

### Faza 6 — Output
- `output/raport_YYYYMMDD_HHMMSS.pbix`
- `output/raport_YYYYMMDD_HHMMSS.md` (log decyzji, anomalie, miary, uwagi reviewera)

---

## Error handling

- Każdy tool zwraca ustrukturyzowany wynik z `status` i `message`
- Reviewer Agent blokuje output przy krytycznych problemach — użytkownik dostaje raport z opisem zamiast uszkodzonego `.pbix`
- Max 2 iteracje feedback-loop; po przekroczeniu — graceful stop z raportem diagnostycznym
- Agent zatrzymuje się i pyta użytkownika tylko przy rzeczywistej niejednoznaczności (np. dwie kolumny o tej samej nazwie semantycznej)

---

## Testowanie

- **Fixtures:** Zestaw przykładowych CSV (sprzedaż Q3, KPI miesięczne, dane czasowe)
- **Testy jednostkowe:** `processor.py` (profilowanie, czyszczenie), `generator.py` (poprawność ZIP → `.pbix`)
- **Test integracyjny end-to-end:** polecenie → `.pbix` → weryfikacja przez otwarcie w Power BI Desktop

---

## Poza zakresem (v1)

- Źródła danych inne niż CSV (SQL, JSON, API)
- Publikacja do Power BI Service / Fabric
- Podgląd dashboardu jako obraz/PDF przed otwarciem
- Obsługa relacji między wieloma plikami CSV
