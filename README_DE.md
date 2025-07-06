# 7 Lebenszyklen KI-Assistent

Ein KI-gestütztes System zur Unterstützung bei Fragen und Affirmationen basierend auf dem 7 Lebenszyklen-Konzept.

## Überblick

Dieses Projekt bietet zwei Hauptfunktionen:

1. **Fragen & Antworten (Q&A)**: Stelle Fragen über die 7 Lebenszyklen und erhalte fundierte Antworten basierend auf der umfassenden Wissensdatenbank.

2. **Affirmationen-Generator**: Erstelle personalisierte Affirmationen für verschiedene Lebensperioden und Zyklen (Tag, Woche, Monat, Jahr, Leben).

## Funktionen

### Q&A Agent
- Beantwortet Fragen über die 7 Lebenszyklen-Philosophie
- Nutzt eine vektorbasierte Suche in der PDF-Wissensdatenbank
- Gibt strukturierte, kontextbezogene Antworten auf Deutsch

### Affirmationen Agent
- Generiert personalisierte Affirmationen für verschiedene Perioden
- Vermeidet Duplikate durch intelligente Speicherung
- Unterstützt verschiedene Themen: Energie, Kreativität, Erfolg, Beziehungen, Wachstum
- Anpassbar an spezifische Phasen (z.B. Morgen, Frühling, Neumond)

## Installation

1. **Backend-Abhängigkeiten installieren:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Frontend-Abhängigkeiten installieren:**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

3. **Umgebungsvariablen setzen:**
   Erstelle eine `.env` Datei im Hauptverzeichnis:
   ```
   OPENAI_API_KEY=dein_openai_api_key
   ```

## Starten der Anwendung

1. **Backend starten:**
   ```bash
   python3 backend/main.py
   ```
   Das Backend läuft auf http://localhost:8000

2. **Frontend starten (in einem neuen Terminal):**
   ```bash
   cd frontend
   npm start
   ```
   Das Frontend läuft auf http://localhost:3000

## Nutzung

### Fragen stellen
1. Gehe zur "Fragen & Antworten" Seite
2. Stelle eine Frage über die 7 Lebenszyklen
3. Erhalte eine detaillierte Antwort basierend auf der Wissensdatenbank

### Affirmationen generieren
1. Gehe zur "Affirmationen" Seite
2. Wähle einen Perioden-Typ (Tag, Woche, Monat, Jahr, Leben)
3. Optional: Wähle eine spezifische Phase
4. Klicke auf "Affirmationen generieren"
5. Die generierten Affirmationen werden gespeichert und angezeigt

## API-Endpunkte

- `POST /ask-question` - Stelle eine Frage
- `GET /knowledge-overview` - Erhalte eine Übersicht der Wissensdatenbank
- `POST /generate-affirmations` - Generiere neue Affirmationen
- `GET /affirmations` - Rufe gespeicherte Affirmationen ab
- `GET /periods` - Erhalte verfügbare Perioden-Typen
- `GET /health` - Überprüfe den System-Status

## Technologie-Stack

- **Backend**: FastAPI, CrewAI, LangChain, FAISS
- **Frontend**: React, TypeScript, Axios
- **KI**: OpenAI GPT-4, Embeddings
- **Datenbank**: FAISS Vektordatenbank für Wissenssuche

## Struktur

```
7cycles-ai/
├── backend/
│   └── main.py              # FastAPI Server
├── src/
│   └── agents/
│       ├── qa_agent.py      # Q&A Agent
│       └── affirmations_agent.py  # Affirmationen Agent
├── frontend/
│   └── src/
│       └── components/
│           ├── QAInterface.tsx      # Q&A Benutzeroberfläche
│           └── AffirmationsInterface.tsx  # Affirmationen Benutzeroberfläche
├── knowledge_files/
│   └── 20250607_7Cycles of Life_Ebook.pdf  # Wissensdatenbank
└── static/
    └── affirmations_storage.json  # Gespeicherte Affirmationen
```