# Product Requirements Document (PRD): rubot

## 1. Ziel

Ein CLI-Tool namens `rubot`, das:

1. Die aktuelle Rathaus-Umschau PDF herunterlädt,
2. mit `marker-pdf` zu Markdown konvertiert,
3. den Inhalt an OpenRouter sendet und
4. das Ergebnis als JSON zurückgibt (stdout oder Datei).

## 2. Funktionale Anforderungen

### 2.1. Datum und URL

- Standard: heutiges Datum (`YYYY-MM-DD`)
- PDF-URL-Format: `https://ru.muenchen.de/pdf/<YYYY>/ru-<YYYY>-<MM>-<DD>.pdf`
- Optional: `--date` zur expliziten Angabe

### 2.2. PDF → Markdown

- PDF wird von oben genannter URL heruntergeladen.
- Umwandlung via `marker-pdf` (im selben Virtualenv installiert)

### 2.3. OpenRouter-API

- POST-Request mit:
  - Markdown als User-Message
  - System-Prompt aus Datei (`--prompt`) oder `.env`
  - Modell per `--model` (Fallback: `.env`, dann Default)
- API-Key via `OPENROUTER_API_KEY`

### 2.4. Ausgabe

- Standard: JSON an `stdout`
- Optional: `--output result.json` für Dateiausgabe

## 3. Nicht-funktionale Anforderungen

| Merkmal            | Beschreibung                                           |
| ------------------ | ------------------------------------------------------ |
| Programmiersprache | Python 3.13+                                           |
| Venv               | `marker-pdf` wird mit `pip` im selben Venv installiert |
| CLI                | `click` (empfohlen)                                    |
| Tests              | `pytest`, mit realitätsnahen Mocks                     |
| GitHub Hosting     | Repository bei GitHub                                  |
| CI/CD              | GitHub Actions für Tests und Docker-Build              |
| Containerisierung  | Alpine-basiertes Python-Dockerfile                     |
| Lizenz             | MIT                                                    |
| Plattform          | Linux/macOS (CLI-basiert)                              |

## 4. CLI-Aufruf

```
rubot [--date YYYY-MM-DD] [--output result.json] [--prompt prompt.txt] [--model model-id]
```

## 5. Beispiel-Workflows auf GitHub

### 5.1. CI (Tests) `.github/workflows/test.yml`

```yaml
name: Test rubot

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.14"
      - run: python -m pip install -r requirements.txt
      - run: pytest
```

### 5.2. Docker Build & Push `.github/workflows/docker.yml`

```yaml
name: Build Docker Image

on:
  push:
    tags:
      - "v*"

jobs:
  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t ghcr.io/rmoriz/rubot:${GITHUB_REF##*/} .
      - run: echo ${{ secrets.GITHUB_TOKEN }} | docker login ghcr.io -u $GITHUB_ACTOR --password-stdin
      - run: docker push ghcr.io/rmoriz/rubot:${GITHUB_REF##*/}
```

## 6. Dockerfile (Beispiel)

```Dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install git+https://github.com/datalab-to/marker.git

ENTRYPOINT ["python", "-m", "rubot"]
```

## 7. Teststrategie

- `pytest` für Unit-Tests
- Verwendung von `unittest.mock` für Netzwerk und Subprozesse
- Integrationstests optional mit echter `marker-pdf`-Installation
