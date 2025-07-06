# Migration zu YAML-basierter CrewAI Konfiguration

## Überblick

Die Agent-Konfiguration wurde von hardcodierter Python-Konfiguration auf YAML-basierte Konfigurationsdateien umgestellt, wie von der CrewAI-Dokumentation empfohlen.

## Änderungen

### Neue Dateien

1. **Konfigurationsdateien**:
   - `src/config/agents.yaml` - Agent-Definitionen
   - `src/config/tasks.yaml` - Task-Definitionen
   - `src/config/crews.yaml` - Crew-Konfigurationen
   - `src/config/tools.yaml` - Tool-Konfigurationen

2. **Basis-Klasse**:
   - `src/crews/base_crew.py` - Basis-Klasse für YAML-Konfiguration

3. **Refaktorierte Agents**:
   - `src/agents/qa_agent_v2.py` - YAML-basierter Q&A Agent
   - `src/agents/affirmations_agent_v2.py` - YAML-basierter Affirmationen Agent

4. **Test-Script**:
   - `test_yaml_config.py` - Testet die YAML-Konfiguration

### Geänderte Dateien

1. **Backend**:
   - `backend/main.py` - Importiert neue Agent-Versionen
   - `requirements.txt` - Fügt PyYAML hinzu

## Vorteile der YAML-Konfiguration

1. **Separation of Concerns**: Konfiguration ist von der Geschäftslogik getrennt
2. **Wartbarkeit**: Einfachere Anpassung von Agent-Eigenschaften ohne Code-Änderungen
3. **Konsistenz**: Folgt den CrewAI Best Practices
4. **Flexibilität**: Verschiedene Konfigurationen für verschiedene Umgebungen möglich
5. **Lesbarkeit**: YAML ist leichter zu lesen und zu verstehen

## YAML-Struktur

### agents.yaml
```yaml
agent_name:
  role: "Agent-Rolle"
  goal: "Agent-Ziel"
  backstory: "Agent-Hintergrund"
  verbose: true
  allow_delegation: false
  max_iter: 3
  max_execution_time: 300
```

### tasks.yaml
```yaml
task_name:
  description: "Task-Beschreibung mit {parameters}"
  expected_output: "Erwartete Ausgabe"
  agent: agent_name
```

### crews.yaml
```yaml
crew_name:
  agents:
    - agent_name
  process: sequential
  verbose: true
  memory: false
  cache: true
  max_rpm: 10
```

## Verwendung

### Agent erstellen
```python
from src.crews.base_crew import BaseCrew

crew = BaseCrew()
agent = crew.create_agent("qa_agent", llm=your_llm)
```

### Task erstellen
```python
task = crew.create_task("answer_question_task", agent, question="Was sind die 7 Lebenszyklen?")
```

### Crew erstellen und ausführen
```python
crew_instance = crew.create_crew("qa_crew", agents=[agent], tasks=[task])
result = crew_instance.kickoff()
```

## Testing

Führe das Test-Script aus um die Konfiguration zu überprüfen:

```bash
python test_yaml_config.py
```

## Migration für neue Agents

1. Erstelle Agent-Definition in `agents.yaml`
2. Erstelle Task-Definitionen in `tasks.yaml`
3. Erstelle Crew-Konfiguration in `crews.yaml`
4. Erbe von `BaseCrew` in deiner Agent-Klasse
5. Nutze `create_agent()`, `create_task()` und `create_crew()` Methoden

## Alte Dateien

Die ursprünglichen Agent-Dateien (`qa_agent.py`, `affirmations_agent.py`) können entfernt werden, sobald die YAML-basierten Versionen getestet und validiert sind.

## Dependencies

Neue Abhängigkeit hinzugefügt:
- `PyYAML>=6.0`