# Projektplan: rubot CLI-Tool

Basierend auf der PRD.md wurden folgende Milestones, Todos und Deliverables definiert:

## Milestones

### Milestone 1: Projekt-Setup und Grundstruktur (2-3 Tage)

**Ziel:** Basis-Projektstruktur und Entwicklungsumgebung einrichten

#### Todos:

- [ ] Python 3.13+ Umgebung einrichten
- [ ] Virtuelle Umgebung erstellen und aktivieren
- [ ] Projektdatenstruktur gemäß PRD erstellen
- [ ] requirements.txt mit Abhängigkeiten erstellen
- [ ] pyproject.toml konfigurieren
- [ ] .env.example mit OpenRouter API Key Template erstellen
- [ ] Git Repository initialisieren
- [ ] .gitignore für Python Projekte erstellen
- [ ] README.md mit Installationsanleitung erstellen

#### Deliverables:

- Komplette Projektstruktur im Verzeichnis
- requirements.txt mit allen Abhängigkeiten
- pyproject.toml mit Projekt-Metadaten
- .env.example Vorlage
- README.md mit Setup-Anleitung
- Git Repository mit ersten Commits

### Milestone 2: Core-Module Implementierung (5-7 Tage)

**Ziel:** Kernfunktionalität der einzelnen Module umsetzen

#### Todos:

- [ ] **downloader.py**: PDF von URL herunterladen
  - [ ] URL-Generierung basierend auf Datum implementieren
  - [ ] HTTP-Client für PDF-Download
  - [ ] Error-Handling für Netzwerkfehler
  - [ ] Tests für downloader.py
- [ ] **marker.py**: PDF zu Markdown Konvertierung
  - [ ] Integration mit marker-pdf Bibliothek
  - [ ] Subprozess-Aufruf implementieren
  - [ ] Error-Handling für Konvertierungsfehler
  - [ ] Tests für marker.py
- [ ] **llm.py**: OpenRouter API Integration
  - [ ] HTTP-Client für OpenRouter API
  - [ ] Prompt-Handling aus Datei und .env
  - [ ] JSON-Antwort Parsing
  - [ ] Error-Handling für API-Fehler
  - [ ] Tests für llm.py
- [ ] **utils.py**: Hilfsfunktionen
  - [ ] Datum-Validierung
  - [ ] Datei-Handling Utilities
  - [ ] Tests für utils.py

#### Deliverables:

- Vollständige Implementierung aller Core-Module
- Unit-Tests für jedes Modul mit >80% Coverage
- Error-Handling für alle Edge-Cases
- Mock-Tests für externe Abhängigkeiten

### Milestone 3: CLI-Interface und Integration (3-4 Tage)

**Ziel:** CLI-Tool mit Click-Framework und Gesamtintegration

#### Todos:

- [ ] **cli.py**: Click-basiertes CLI implementieren
  - [ ] Argument-Parsing für --date, --output, --prompt, --model
  - [ ] Default-Werte und Validierung
  - [ ] Hilfe-Texte und Usage-Dokumentation
- [ ] ****main**.py**: Entry-Point konfigurieren
  - [ ] Python-Modul als ausführbares CLI
  - [ ] Error-Handling für CLI-Aufrufe
- [ ] Integration aller Module
  - [ ] Workflow: Download → Convert → LLM → Output
  - [ ] Temporäre Datei-Handling
  - [ ] JSON-Ausgabe formatieren
- [ ] End-to-End Tests
  - [ ] CLI-Tests mit pytest-click
  - [ ] Integration-Tests für gesamten Workflow

#### Deliverables:

- Vollständig funktionierendes CLI-Tool
- Dokumentation aller CLI-Optionen
- Integration-Tests für gesamten Workflow
- Beispiel-Ausgaben und Usage-Dokumentation

### Milestone 4: Testing und CI/CD (2-3 Tage)

**Ziel:** Automatisierte Tests und Continuous Integration

#### Todos:

- [ ] **GitHub Actions Setup**
  - [ ] .github/workflows/test.yml erstellen
  - [ ] Python 3.13 CI-Umgebung konfigurieren
  - [ ] pytest in CI integrieren
  - [ ] Code Coverage Reports
- [ ] **Test-Erweiterung**
  - [ ] Mock-Tests für externe APIs
  - [ ] Edge-Case Tests
  - [ ] Performance-Tests für große PDFs
- [ ] **Code-Quality**
  - [ ] Linting mit flake8/black
  - [ ] Type-Checking mit mypy
  - [ ] Pre-commit hooks einrichten

#### Deliverables:

- Vollständige CI/CD Pipeline
- Automatisierte Tests bei jedem Push/PR
- Code-Coverage Reports
- Linting und Type-Checking

### Milestone 5: Containerisierung und Release (2-3 Tage)

**Ziel:** Docker-Container und öffentlicher Release

#### Todos:

- [ ] **Dockerfile**
  - [ ] Alpine-basiertes Python 3.13 Image
  - [ ] marker-pdf Installation integrieren
  - [ ] Multi-Stage Build für kleines Image
  - [ ] Security-Scanning
- [ ] **GitHub Container Registry**
  - [ ] .github/workflows/docker.yml erstellen
  - [ ] Automatisches Build und Push bei Tags
  - [ ] GHCR Login und Push konfigurieren
- [ ] **Release Management**
  - [ ] Git Tags und Releases
  - [ ] Changelog erstellen
  - [ ] Installationsanleitung aktualisieren

#### Deliverables:

- Docker-Image auf GHCR
- Automatisierte Releases bei Git Tags
- Vollständige Installationsanleitung
- Beispiel-Docker-Usage

## Zeitplan Gesamt

- **Gesamtdauer:** 14-20 Arbeitstage
- **Kritische Pfad:** Milestone 2 (Core-Module) ist der längste
- **Parallelisierung:** Milestone 4 und 5 können parallel zu 2 und 3 bearbeitet werden

## Abhängigkeiten

- **Extern:** marker-pdf (datalab-to/marker), OpenRouter API
- **Intern:** Alle Module müssen sequentiell implementiert werden (Download → Convert → LLM)

## Risiken und Mitigation

- **marker-pdf Installation:** Docker-Build könnte komplex werden → Multi-Stage Build
- **OpenRouter API Limits:** Rate-Limiting implementieren
- **Große PDFs:** Streaming und Memory-Management
- **Netzwerkfehler:** Retry-Mechanismen und Caching

## Erfolgsmessung

- Alle Tests grün
- Docker-Image < 500MB
- CLI funktioniert ohne externe Konfiguration
- JSON-Ausgabe validiert
