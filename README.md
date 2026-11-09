# Lethe Privacy Gateway

Lethe ist ein mandantenfähiger REST-Dienst zur Pseudonymisierung und Wiederherstellung personenbezogener Angaben in Texten. Die Erkennung kombiniert das deutsche spaCy-Modell, reguläre Ausdrücke und mandantenspezifische Wörterbücher. Die API basiert auf FastAPI und speichert Zuordnungen für die Wiederherstellung vorübergehend im Arbeitsspeicher.

## Funktionen

- Erkennt unter anderem Personen, Organisationen, Orte, Aktenzeichen, Telefonnummern, E-Mail-Adressen, Postleitzahlen, Steuer-IDs, IBANs, BICs und Datumsangaben.
- Ersetzt erkannte Werte durch Platzhalter wie `[PER_1]` und verwendet Tags innerhalb eines Textes konsistent.
- Kann Texte anhand einer Session-ID wiederherstellen. Sessions sind mandantengebunden, laufen nach einer Stunde ab und gehen bei einem Neustart des Prozesses verloren.
- Verwaltet mandantenspezifische Wörterbücher mit den Kategorien `PER`, `ORG`, `LOC`, `MISC`, `SKIP` und `CASE_NR`.
- Extrahiert Text aus TXT, Markdown, DOCX, ODT und PDF.
- Begrenzt Anfragen pro IP: in der Regel 60 pro Minute, beim Datei-Upload 15 pro Minute.

## Voraussetzungen

- Python 3.10 oder neuer
- MariaDB/MySQL mit Unix-Socket unter `/var/run/mysqld/mysqld.sock`
- Eine vorbereitete Datenbank `lethe_privacy` mit dem benötigten Schema
- Genügend Arbeitsspeicher und Speicherplatz für das große deutsche spaCy-Modell `de_core_news_lg`

Das SQL-Exportfile `lethe.sql` enthält `DROP TABLE`-Anweisungen. Importieren Sie es nur in eine geeignete, gesicherte Datenbank und prüfen Sie den Inhalt vor dem Ausführen. Die Anwendung benötigt mindestens die Tabellen `admin_auth`, `client_auth`, `api_logs`, `error_logs`, `lethe_dictionary` und `lethe_system_dictionary`.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Die Abhängigkeiten installieren spaCy und das Modell `de_core_news_lg` zusammen. Stellen Sie sicher, dass die MariaDB-Datenbank, das Schema und die erforderlichen aktiven Clients eingerichtet sind.

## Konfiguration

Legen Sie im Projektverzeichnis eine `.env`-Datei an. Sie wird beim Start geladen und darf nicht eingecheckt werden.

```dotenv
LETHE_SECRET_KEY=<zufälliger-geheimer-wert>
LETHE_SECRET_DICTIONARY_KEY=<anderer-zufälliger-geheimer-wert>
LETHE_DB_USER=lethe
LETHE_ADMIN_API_KEY=<administrator-api-schlüssel>
LETHE_ALLOWED_ORIGINS=http://localhost:8000,tauri://localhost
```

`LETHE_SECRET_KEY` und `LETHE_SECRET_DICTIONARY_KEY` sind erforderlich; ohne sie startet der Dienst nicht. Verwenden Sie starke, voneinander unabhängige Geheimnisse und bewahren Sie diese dauerhaft sicher auf, da sie für den Zugriff auf gespeicherte Wörterbucheinträge benötigt werden. `LETHE_DB_USER` ist optional und fällt auf `lethe` zurück. `LETHE_ADMIN_API_KEY` wird vom Admin-Key-Mechanismus gelesen; die aktuell bereitgestellten Endpunkte verwenden für die Konfigurationsneuladung stattdessen einen aktiven Datenbank-Admin mit `X-Access-Code`. `LETHE_ALLOWED_ORIGINS` ist optional; mehrere Origins werden kommasepariert angegeben.

Die NLP-Konfiguration wird aus `nlp_config.json` im aktuellen Arbeitsverzeichnis geladen. Die Datenbankverbindung erfolgt über den fest codierten MariaDB-Unix-Socket; es gibt keine Umgebungsvariablen für Host, Port oder Datenbanknamen.

## Start

Im Projektverzeichnis:

```bash
uvicorn main:app --host 127.0.0.1 --port 8000
```

Für den Produktivbetrieb sollte TLS über einen geeigneten Reverse Proxy oder eine entsprechend konfigurierte Uvicorn-Instanz bereitgestellt und der Dienst nicht ungeschützt öffentlich exponiert werden.

- OpenAPI-Dokumentation: `http://127.0.0.1:8000/docs`
- Statusprüfung: `GET /v1/health` (ohne Authentifizierung)

## API

Geschützte Endpunkte erwarten den Header `X-Access-Code`. Der Code wird gegen einen aktiven Eintrag in `admin_auth` geprüft; der zugehörige Client muss ebenfalls aktiv und noch gültig sein. Anfragen sind auf den jeweiligen Client beschränkt.

### Text anonymisieren

`POST /v1/anonymize`

```bash
curl -X POST http://127.0.0.1:8000/v1/anonymize \
  -H 'Content-Type: application/json' \
  -H 'X-Access-Code: <freischaltcode>' \
  -d '{"text":"Sabine wohnt in München."}'
```

Antwort:

```json
{
  "session_id": "<uuid>",
  "anonymized_text": "[PER_1] wohnt in [LOC_1]."
}
```

Das Textlimit stammt aus `client_auth.max_text_length` (Standard-Fallback: 100.000 Zeichen; `0` bedeutet unbegrenzt).

### Text wiederherstellen

`POST /v1/deanonymize`

```json
{
  "session_id": "<uuid-aus-der-anonymisierung>",
  "text": "[PER_1] wohnt in [LOC_1]."
}
```

Die Antwort enthält den wiederhergestellten Text unter `text`. Eine Session kann nur vom Client verwendet werden, der sie erzeugt hat, und wird nach erfolgreicher Wiederherstellung gelöscht.

### Wörterbuch verwalten

- `POST /v1/dictionary/add` – JSON mit `term` und `category`
- `DELETE /v1/dictionary/remove` – JSON mit `term` und `category`
- `GET /v1/dictionary/list` – listet die Einträge des authentifizierten Clients

Einträge werden mandantengetrennt gespeichert. Begriffe werden verschlüsselt gespeichert; für exakte Datenbankabfragen wird ein HMAC-Blindindex verwendet.

### Dokumenttext extrahieren

`POST /v1/extract-text` erwartet einen Multipart-Upload mit dem Feld `file`. Unterstützt werden `.txt`, `.md`, `.docx`, `.odt` und `.pdf`. Das Dateilimit stammt aus `client_auth.max_file_size_mb` (Standard-Fallback: 20 MB; `0` bedeutet unbegrenzt). Die Antwort enthält den extrahierten Text unter `text`.

### Konfiguration neu laden

`POST /v1/admin/config/reload` lädt `nlp_config.json` und das System-Wörterbuch neu. Erfordert einen aktiven System-Admin-Code im `X-Access-Code`-Header und muss lokal auf dem Server aufgerufen werden.

## Tests

`test_api.py` ist ein Integrationstest-Client für einen laufenden Gateway-Server. Vor dem Ausführen müssen `BASE_URL` und `ACCESS_CODE` in der Datei zur lokalen Testumgebung passen. Der Client deaktiviert die TLS-Zertifikatsprüfung und ist ausschließlich für lokale Tests mit selbstsignierten Zertifikaten vorgesehen.

## Lizenz

Dieses Projekt steht unter der Apache License 2.0. Siehe [LICENSE](LICENSE).
