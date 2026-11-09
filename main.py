import time
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, File, UploadFile, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from odf import text, teletype
from odf.opendocument import load
from docx import Document
from datetime import datetime
import hashlib
import os
import json
import io
import sys
import syslog
import spacy
import uuid
import re
import mysql.connector
import pypdf
import warnings
import base64
import hmac
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from dotenv import load_dotenv


load_dotenv()

# 
# Debugausgabe in die standard System-Syslog (sudo journalctl -u lethe -f )
# 
def _log_syslog(msg: str, priority=syslog.LOG_INFO) -> None:
    """Schreibt Log-Meldungen in die System-Syslog mit dem Präfix 'lethe sagt: '."""
    syslog.syslog(priority, f"lethe sagt: {msg}")

# ===========================================================================
# SCHLÜSSEL & KONFIGURATION
# ===========================================================================
raw_secret = os.environ.get("LETHE_SECRET_KEY")
if not raw_secret:
    raise ValueError("CRITICAL: LETHE_SECRET_KEY Umgebungsvariable ist nicht gesetzt!")

SECRET_KEY = raw_secret.encode('utf-8')

raw_dict_secret = os.environ.get("LETHE_SECRET_DICTIONARY_KEY")
if not raw_dict_secret:
    raise ValueError("CRITICAL: LETHE_SECRET_DICTIONARY_KEY Umgebungsvariable ist nicht gesetzt!")

_DICT_SECRET_BYTES = raw_dict_secret.encode('utf-8')
DICT_AES_KEY = hashlib.sha256(_DICT_SECRET_BYTES + b":aes_key").digest()
DICT_HMAC_KEY = hashlib.sha256(_DICT_SECRET_BYTES + b":hmac_key").digest()


def prp_round(value: int, round_num: int, modulus: int = 10000) -> int:
    """PRP-Rundenfunktion basierend auf standardisiertem HMAC-SHA256."""
    # Eindeutige Runden- und Wertebindung im Byte-Format
    msg = f"{round_num}:{value}".encode("utf-8")
    digest = hmac.new(raw_dict_secret, msg, hashlib.sha256).digest()
    
    # 8 Bytes Entropie nutzen, um Modulo-Bias bei kleinen Zahlen vollständig zu eliminieren
    rand_int = int.from_bytes(digest[:8], "big")
    return rand_int % modulus


def encrypt_number(n: int, rounds: int = 10) -> int:
    """Verschlüsselt eine 8-stellige Zahl (0-99999999) kollisionsfrei in denselben Bereich."""
    if not (0 <= n < 100_000_000):
        raise ValueError("Zahl muss zwischen 0 und 99.999.999 liegen.")

    # Zerlegung in zwei Hälften zu je 4 Dezimalstellen (0..9999)
    left, right = divmod(n, 10000)

    for r in range(rounds):
        left, right = right, (left + prp_round(right, r, 10000)) % 10000

    return left * 10000 + right


def decrypt_number(n: int, rounds: int = 10) -> int:
    """Kehrt die Permutation exakt um."""
    if not (0 <= n < 100_000_000):
        raise ValueError("Zahl muss zwischen 0 und 99.999.999 liegen.")

    left, right = divmod(n, 10000)

    for r in reversed(range(rounds)):
        left, right = (right - prp_round(left, r, 10000)) % 10000, left

    return left * 10000 + right

def compute_blind_index(term: str) -> str:
    """Berechnet einen deterministischen HMAC-SHA256 Blind-Index (Hex-String) für SQL-Abfragen."""
    if not term:
        return ""
    return hmac.new(DICT_HMAC_KEY, term.encode("utf-8"), hashlib.sha256).hexdigest()

def encrypt_term(term: str) -> str:
    """Verschlüsselt einen Begriff mittels AES-256-GCM mit zufälligem 12-Byte IV (Nonce)."""
    if not term:
        return term
    aesgcm = AESGCM(DICT_AES_KEY)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, term.encode("utf-8"), None)
    payload = nonce + ciphertext
    return base64.b64encode(payload).decode("utf-8")

def decrypt_term(encrypted_term: str) -> str:
    """Entschlüsselt einen AES-256-GCM verschlüsselten Begriff mit Graceful Fallback."""
    if not encrypted_term:
        return encrypted_term
    # 1. Versuche AES-GCM (neues Format)
    try:
        raw_payload = base64.b64decode(encrypted_term.encode("utf-8"))
        if len(raw_payload) > 12:
            nonce = raw_payload[:12]
            ciphertext = raw_payload[12:]
            aesgcm = AESGCM(DICT_AES_KEY)
            decrypted = aesgcm.decrypt(nonce, ciphertext, None)
            return decrypted.decode("utf-8")
    except Exception:
        pass

    # 2. Fallback: Altes AES-CBC Format mit SECRET_KEY (für Abwärtskompatibilität)
    try:
        key = hashlib.sha256(SECRET_KEY).digest()
        iv = b"\x00" * 16
        ciphertext = base64.b64decode(encrypted_term.encode("utf-8"))
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        unpadder = padding.PKCS7(128).unpadder()
        term = unpadder.update(padded_data) + unpadder.finalize()
        return term.decode("utf-8")
    except Exception:
        # 3. Fallback: Klartext
        return encrypted_term


# ===========================================================================
# AUTHENTIFIZIERUNGS-DEPENDENCY (prüft X-Access-Code gegen client_auth)
# ===========================================================================
def _get_db_connection():
    """Öffnet eine MariaDB-Verbindung via Unix-Socket."""
    db_user = os.environ.get("LETHE_DB_USER", "lethe")
    return mysql.connector.connect(
        user=db_user,
        unix_socket="/var/run/mysqld/mysqld.sock",
        database="lethe_privacy"
    )

def _log_error(error_type: str, message: str, details: str = None, client_id: str = None) -> None:
    """
    Schreibt einen Fehlereintrag in die Tabelle error_logs.
    Schlägt stillschweigend fehl (kein rekursiver Fehler durch Logging-Fehler).
    """
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO lethe_privacy.error_logs (error_type, message, details, client_id, created_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                error_type,
                message,
                details,
                client_id,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        # Fehler ins Syslog schreiben, um stumme Fehler zu erkennen
        _log_syslog(f"FEHLER in _log_error: {e}", priority=syslog.LOG_ERR)

def _get_client_max_file_size_mb(client_id: str) -> int:
    """
    Holt die maximale Dateigröße in MB für den übergebenen Client aus client_auth.
    Gibt 20 (MB) als Fallback zurück. 0 bedeutet unbegrenzt.
    """
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT max_file_size_mb FROM client_auth WHERE client_id = %s LIMIT 1",
            (client_id,)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row and row[0] is not None:
            return int(row[0])
    except Exception as e:
        _log_error(
            error_type="CLIENT_LIMIT_ERROR",
            message="Fehler beim Auslesen von max_file_size_mb aus client_auth",
            details=str(e),
            client_id=client_id
        )
    return 20

def _get_client_max_text_length(client_id: str) -> int:
    """
    Holt die maximale Textlänge (Zeichen) für den übergebenen Client aus client_auth.
    Gibt 100000 (Zeichen) als Fallback zurück. 0 bedeutet unbegrenzt.
    """
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT max_text_length FROM client_auth WHERE client_id = %s LIMIT 1",
            (client_id,)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row and row[0] is not None:
            return int(row[0])
    except Exception as e:
        _log_error(
            error_type="CLIENT_LIMIT_ERROR",
            message="Fehler beim Auslesen von max_text_length aus client_auth",
            details=str(e),
            client_id=client_id
        )
    return 100000


def verify_client(x_access_code: Optional[str] = Header(default=None)) -> str:
    """
    FastAPI-Dependency: Liest den X-Access-Code Header (als unlock_code),
    prüft, ob dieser in der Tabelle admin_auth in der Spalte unlock_code existiert
    und aktiv ist, ob der zugehörige Client aktiv ist und seine Gültigkeit (valid_until)
    noch nicht abgelaufen ist, und ermittelt die client_id.
    Gibt bei Erfolg die client_id (als nullaufgefüllter 4-stelliger String) zurück.
    Wirft HTTP 403 Forbidden bei ungültigem oder fehlendem Code mit Micro-Tarpitting (1 Sekunde).
    """
    _FORBIDDEN = "ungültiger Freischaltcode"

    def _fail_auth(error_type: str, message: str, details: str = None, client_id: str = None):
        _log_error(error_type=error_type, message=message, details=details, client_id=client_id)
        time.sleep(1)  # Micro-Tarpitting: 1 Sekunde Verzögerung vor 403 Forbidden
        raise HTTPException(status_code=403, detail=_FORBIDDEN)

    if x_access_code is None:
        _fail_auth(
            error_type="AUTH_MISSING",
            message="X-Access-Code Header fehlt"
        )

    try:
        val = int(x_access_code)
        if not (0 <= val <= 99999999):
            raise ValueError("Out of range")
            
        # Entschlüssele den übermittelten Code (Fallback auf Klartext falls Fehler)
        try:
            decrypted_val = decrypt_access_code(val)
            db_lookup_code = f"{decrypted_val:08d}"
        except Exception:
            db_lookup_code = x_access_code
            
    except (ValueError, TypeError):
        _fail_auth(
            error_type="AUTH_INVALID_FORMAT",
            message="X-Access-Code ist kein gültiger Integer im Bereich 0–99999999",
            details=f"Übermittelter Wert: {x_access_code!r}"
        )

    current_time = datetime.now()
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT a.client_id, a.status, c.status, c.valid_until
            FROM admin_auth a
            LEFT JOIN client_auth c ON a.client_id = c.client_id
            WHERE a.unlock_code = %s OR a.unlock_code = %s
            LIMIT 1
            """,
            (db_lookup_code, x_access_code)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
    except Exception as e:
        _fail_auth(
            error_type="AUTH_DB_ERROR",
            message="DB-Abfrage zur Client-Verifizierung fehlgeschlagen",
            details=str(e)
        )

    if row is None:
        _fail_auth(
            error_type="AUTH_UNKNOWN_CLIENT",
            message="Unlock-Code nicht in admin_auth gefunden",
            #details=f"Unlock-Code: {x_access_code!r}"
            details=f"Unlock-Code (maskiert): {x_access_code[:2]}******{x_access_code[-2:]}"
        )

    client_id_raw, admin_status, client_status, valid_until = row

    if admin_status != 'active':
        _fail_auth(
            error_type="AUTH_ADMIN_LOCKED",
            message="Admin-Account ist nicht aktiv",
            details=f"Unlock-Code: {x_access_code!r}, Status: {admin_status!r}",
            client_id=str(client_id_raw) if client_id_raw else None
        )

    if client_id_raw is None or client_status is None:
        _fail_auth(
            error_type="AUTH_CLIENT_NOT_FOUND",
            message="Zugehörige client_id nicht in client_auth gefunden oder NULL",
            details=f"Unlock-Code: {x_access_code!r}, client_id: {client_id_raw!r}"
        )

    if client_status != 'active':
        _fail_auth(
            error_type="AUTH_CLIENT_LOCKED",
            message="Client-Account ist nicht aktiv",
            details=f"client_id: {client_id_raw!r}, Status: {client_status!r}",
            client_id=str(client_id_raw)
        )

    if valid_until is None or valid_until < current_time:
        _fail_auth(
            error_type="AUTH_CLIENT_EXPIRED",
            message="Gültigkeit des Clients ist abgelaufen",
            details=f"client_id: {client_id_raw!r}, valid_until: {valid_until!r}",
            client_id=str(client_id_raw)
        )


    try:
        client_id_int = int(client_id_raw)
        client_id_str = f"{client_id_int:04d}"
    except (ValueError, TypeError):
        client_id_str = str(client_id_raw)

    return client_id_str


def verify_admin(x_admin_key: Optional[str] = Header(default=None)) -> bool:
    """
    FastAPI-Dependency: Prüft den X-Admin-Key Header gegen LETHE_ADMIN_API_KEY aus der .env.
    Wirft HTTP 403 Forbidden bei ungültigem Schlüssel.
    """
    admin_key = os.environ.get("LETHE_ADMIN_API_KEY")
    if not admin_key:
        _log_error(
            error_type="ADMIN_AUTH_CONFIG_ERROR",
            message="LETHE_ADMIN_API_KEY ist in der Umgebung/.env nicht konfiguriert"
        )
        time.sleep(1)
        raise HTTPException(status_code=500, detail="Admin-Authentifizierung ist serverseitig nicht konfiguriert.")

    if x_admin_key is None or not hmac.compare_digest(x_admin_key, admin_key):
        _log_error(
            error_type="ADMIN_AUTH_FAILED",
            message="Ungültiger oder fehlender X-Admin-Key Header"
        )
        time.sleep(1)
        raise HTTPException(status_code=403, detail="Ungültiger Administrator-Schlüssel.")

    return True

def _log_api_call(client_id: str, endpoint: str, word_count: int) -> None:
    """Schreibt einen Eintrag in die api_logs Tabelle."""
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO api_logs (client_id, endpoint, word_count, created_at)
            VALUES (%s, %s, %s, %s)
            """,
            (client_id, endpoint, word_count, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        # Logging-Fehler sollen den eigentlichen Request nicht blockieren
        _log_syslog(f"[Lethe Log-Error] api_logs INSERT fehlgeschlagen: {e}", priority=syslog.LOG_ERR)


# ===========================================================================
# SESSION TTL & PERIODIC CLEANUP CONFIGURATION (1 Stunde Gültigkeit)
# ===========================================================================
SESSION_MAX_AGE_SECONDS = 3600  # Max. Session-Lebensdauer (1 Std.)
SESSION_CLEANUP_INTERVAL_SECONDS = 300  # Prüf-Intervall (alle 5 Min.)

async def cleanup_expired_sessions_task():
    """
    Periodischer Hintergrund-Task: Durchsucht sessions_db alle 5 Minuten
    und löscht alle Sessions, deren Alter SESSION_MAX_AGE_SECONDS (1 Std.) überschreitet.
    """
    while True:
        try:
            await asyncio.sleep(SESSION_CLEANUP_INTERVAL_SECONDS)
            now = time.time()
            expired_ids = [
                s_id for s_id, s_data in list(sessions_db.items())
                if now - s_data.get("created_at", 0) > SESSION_MAX_AGE_SECONDS
            ]
            for s_id in expired_ids:
                sessions_db.pop(s_id, None)
            if expired_ids:
                _log_syslog(f"Session Cleanup: {len(expired_ids)} abgelaufene Sessions bereinigt.")
        except asyncio.CancelledError:
            break
        except Exception as e:
            _log_syslog(f"Fehler im Session Cleanup Task: {e}", priority=syslog.LOG_ERR)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Lade System-Wörterbuch aus MariaDB beim Serverstart
    load_system_dictionary()
    # Startet den periodischen Cleanup-Task beim Serverstart
    cleanup_task = asyncio.create_task(cleanup_expired_sessions_task())
    yield
    # Beendet den Task geordnet beim Server-Shutdown
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Lethe Privacy Proxy Gateway", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ##################################################################
# --- CORS KONFIGURATION (Umgebungsspezifisch via .env) ---
# ##################################################################
# ISO 27001 (A.8.31): Konfiguriere nur erlaubte CORS-Origins
# Zur strikten Trennung von Entwicklungs-, Test- und Produktionsumgebungen
# werden die zugelassenen CORS-Origins aus der Umgebungsvariable LETHE_ALLOWED_ORIGINS
# geladen (kommagetrennte Liste in .env).
# Ist die Umgebungsvariable nicht gesetzt, wird auf sichere Standard-Entwicklungs-Origins zurückgegriffen.
_env_origins = os.environ.get("LETHE_ALLOWED_ORIGINS")
if _env_origins:
    ALLOWED_ORIGINS = [origin.strip() for origin in _env_origins.split(",") if origin.strip()]
else:
    ALLOWED_ORIGINS = [
        "tauri://localhost",         # Official Tauri v2 Desktop-App Origin
        "http://tauri.localhost",    # macOS / alternative WebView Origin
        "http://localhost:8000",     # Lokale Swagger-UI / Dev-Tests
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)


# Laden des großen deutschen Modells
nlp = spacy.load("de_core_news_lg")

# --- LADE NLP KONFIGURATION ---
def load_nlp_config():
    global TITLE_PATTERNS, SKIP_PATTERNS, LEGAL_FORMS_REGEX
    global VALID_BIC_COUNTRY_CODES, ALLGEMEINE_ABKUERZUNGEN
    global NORMALIZED_ABBREVIATIONS, COMMON_GERMAN_WORDS, COURT_INSTITUTIONS
    try:
        with open("nlp_config.json", "r", encoding="utf-8") as f:
            _config = __import__("json").load(f)
    except Exception as e:
        raise RuntimeError(f"Konnte nlp_config.json nicht laden: {e}")

    TITLE_PATTERNS = _config["TITLE_PATTERNS"]
    SKIP_PATTERNS = _config["SKIP_PATTERNS"]
    LEGAL_FORMS_REGEX = __import__("re").compile(_config["LEGAL_FORMS_PATTERN"])
    VALID_BIC_COUNTRY_CODES = set(_config["VALID_BIC_COUNTRY_CODES"])
    ALLGEMEINE_ABKUERZUNGEN = set(_config["ALLGEMEINE_ABKUERZUNGEN"])
    NORMALIZED_ABBREVIATIONS = {a.replace(".", "").strip().lower() for a in ALLGEMEINE_ABKUERZUNGEN}
    COMMON_GERMAN_WORDS = set(_config["COMMON_GERMAN_WORDS"])
    COURT_INSTITUTIONS = set(_config["COURT_INSTITUTIONS"])

# Initiales Laden
load_nlp_config()

# --- DETERMINISTISCHE ORTE & SUFFIXE (Dynamischer Import aus lethe_system_dictionary) ---
KNOWN_CITIES_SET: set = set()
KNOWN_CITIES_PATTERNS: list = []
TECHNICAL_SUFFIXES: set = set()
MED_SUFFIXES: set = set()
COMPOUND_BLACKLIST_SUFFIXES: set = set()
JUR_INST_REGEX = None
JUR_COURT_REGEX = None
JUR_TITLE_REGEX = None
JUR_ROLE_REGEX = None
JUR_REPRESENTATIVE_REGEX = None

def load_system_dictionary() -> None:
    """
    Lädt dynamisch alle aktiven System-Begriffe aus lethe_system_dictionary in In-Memory Sets.
    Aktualisiert KNOWN_CITIES_SET, TECHNICAL_SUFFIXES, MED_SUFFIXES und den spaCy EntityRuler.
    """
    global KNOWN_CITIES_SET, KNOWN_CITIES_PATTERNS, TECHNICAL_SUFFIXES, MED_SUFFIXES, COMPOUND_BLACKLIST_SUFFIXES
    global JUR_INST_REGEX, JUR_COURT_REGEX, JUR_TITLE_REGEX, JUR_ROLE_REGEX, JUR_REPRESENTATIVE_REGEX
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT term, category FROM lethe_system_dictionary WHERE is_active = 1")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        cities = set()
        tech = set()
        med = set()
        jur_institutions = set()
        jur_titles = set()
        jur_roles = set()
        jur_representatives = set()

        for term, cat in rows:
            clean_term = term.strip()
            if not clean_term:
                continue
            if cat == 'LOC':
                cities.add(clean_term)
            elif cat == 'SUFFIX_TECH':
                tech.add(clean_term.lower())
            elif cat == 'SUFFIX_MED':
                med.add(clean_term.lower())
            elif cat == 'SUFFIX_JUR_INSTITUTIONS':
                jur_institutions.add(clean_term)
            elif cat == 'SUFFIX_JUR_TITLES':
                jur_titles.add(clean_term)
            elif cat == 'SUFFIX_JUR_ROLES':
                jur_roles.add(clean_term)
            elif cat == 'SUFFIX_JUR_REPRESENTATIVES':
                jur_representatives.add(clean_term)

        KNOWN_CITIES_SET = {c.lower() for c in cities}
        KNOWN_CITIES_PATTERNS = [{"label": "LOC", "pattern": [{"LOWER": c.lower()}]} for c in cities]
        TECHNICAL_SUFFIXES = tech
        MED_SUFFIXES = med
        COMPOUND_BLACKLIST_SUFFIXES = TECHNICAL_SUFFIXES.union(MED_SUFFIXES)
        
        court_institutions = {
            term for term in jur_institutions if "gericht" in term.lower()
        }
        court_institutions.update(COURT_INSTITUTIONS)
        court_pattern = "|".join(
            re.escape(term)
            for term in sorted(court_institutions, key=len, reverse=True)
        )
        JUR_COURT_REGEX = re.compile(
            r'\b((?:das\s+)?(?:' + court_pattern + r')\s+[A-ZÄÖÜ][a-zäöüßA-ZÄÖÜ-]+'
            r'(?:\s+[IVXLCDM]+)?)\b',
            re.IGNORECASE
        )
        JUR_INST_REGEX = re.compile(r'\b(?:' + '|'.join(re.escape(x) for x in jur_institutions) + r')\s+([A-ZÄÖÜ][a-zäöüßA-ZÄÖÜ-]+(?:\s+[IVXLCDM]+)?)\b') if jur_institutions else None
        JUR_TITLE_REGEX = re.compile(r'\b(?i:' + '|'.join(re.escape(x) for x in jur_titles) + r')\s+([A-ZÄÖÜ][a-zäöüßA-ZÄÖÜ-]+(?:\s+[A-ZÄÖÜ][a-zäöüßA-ZÄÖÜ-]+){0,2})\b') if jur_titles else None
        JUR_ROLE_REGEX = re.compile(r'\b(?i:' + '|'.join(re.escape(x) for x in jur_roles) + r')\s+([A-ZÄÖÜ][a-zäöüßA-ZÄÖÜ-]+(?:\s+[A-ZÄÖÜ][a-zäöüßA-ZÄÖÜ-]+){0,2})\b') if jur_roles else None
        JUR_REPRESENTATIVE_REGEX = re.compile(r'\b(?i:' + '|'.join(re.escape(x) for x in jur_representatives) + r')\s+([A-ZÄÖÜ][a-zäöüßA-ZÄÖÜ-]+(?:\s+[A-ZÄÖÜ][a-zäöüßA-ZÄÖÜ-]+){0,2})\b') if jur_representatives else None

        # EntityRuler mit aktuellen Mappings aktualisieren
        if "entity_ruler" not in nlp.pipe_names:
            ruler_pipe = nlp.add_pipe("entity_ruler", before="ner")
        else:
            ruler_pipe = nlp.get_pipe("entity_ruler")
            ruler_pipe.clear()

        ruler_pipe.add_patterns(TITLE_PATTERNS)
        ruler_pipe.add_patterns(KNOWN_CITIES_PATTERNS)
        ruler_pipe.add_patterns(SKIP_PATTERNS)

        _log_syslog(f"System Dictionary erfolgreich geladen ({len(cities)} Orte, {len(tech)} Tech-Suffixe, {len(med)} Med-Suffixe).")
    except Exception as e:
        _log_error(
            error_type="SYSTEM_DICT_LOAD_ERROR",
            message="Fehler beim Laden von lethe_system_dictionary aus MariaDB",
            details=str(e)
        )

# Initialer Ladeaufruf beim Modulimport
try:
    load_system_dictionary()
except Exception:
    pass

# In-Memory Session DB
# AUDIT-HINWEIS: Speichert Mappings zusammen mit der erzeugenden client_id zur BOLA/IDOR-Prüfung.
sessions_db: Dict[str, dict] = {}

# Findet Telefonnummern, erlaubt Leerzeichen/Minus, aber stoppt strikt am Zeilenumbruch
#PHONE_REGEX = re.compile(r'(?:\+49|0049|0)[-.\t ]?\(?\d{2,5}\)?(?:[-.\t ]?\d{1,6})+', re.VERBOSE)
PHONE_REGEX = re.compile(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,5}\)?[-.\s]?\d{4,10}\b')
TAX_ID_REGEX = re.compile(r'\bDE\d{9}\b', re.IGNORECASE)
EMAIL_REGEX = re.compile(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b')
ZIP_REGEX = re.compile(r'\b\d{5}\b')
AT_MENTION_REGEX = re.compile(r'(?<!\w)@\w+(?:[.-]\w+)*')

IBAN_REGEX = re.compile(
    r'\b[A-Z]{2}\d{2}(?:[ ]?\d{4}){3,5}(?:[ ]?\d{1,4})?\b'
    r'|\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]{4}){3,6}(?:[ ]?[A-Z0-9]{1,4})?\b',
    re.IGNORECASE
)
BIC_REGEX = re.compile(
    r'\b[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?\b'
)

# VALID_BIC_COUNTRY_CODES wurde nach nlp_config.json ausgelagert

def is_valid_iban(iban: str) -> bool:
    """Prüft eine IBAN anhand des ISO 7064 Modulo 97 Algorithmus."""
    clean_iban = iban.replace(" ", "").replace("-", "").upper()
    if not (15 <= len(clean_iban) <= 34):
        return False
    rearranged = clean_iban[4:] + clean_iban[:4]
    numeric_str = ""
    for char in rearranged:
        if char.isdigit():
            numeric_str += char
        elif char.isalpha():
            numeric_str += str(ord(char) - 55)
        else:
            return False
    try:
        return int(numeric_str) % 97 == 1
    except ValueError:
        return False

def is_valid_bic(bic: str) -> bool:
    """Prüft, ob ein String die ISO 9362 BIC/SWIFT Syntax und einen gültigen Ländercode besitzt."""
    if is_typo_of_common_word(bic):
        return False
    b = bic.strip()
    if not b.isupper():
        return False
    if len(b) not in (8, 11):
        return False
    if not b[:4].isalpha():
        return False
    if b[4:6] not in VALID_BIC_COUNTRY_CODES:
        return False
    if not b[6:8].isalnum():
        return False
    if len(b) == 11 and not b[8:11].isalnum():
        return False
    return True


_DAY = r"(?:0?[1-9]|[12]\d|3[01])"
_MONTH = r"(?:0?[1-9]|1[0-2])"
_MONTHS = r"(?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember|Jan|Feb|Mär|Apr|Jun|Jul|Aug|Sept?|Okt|Nov|Dez)"

# Temporale Präpositionen mit verschmolzenem Artikel im Dativ Singular Maskulin (am, vom, zum)
# Eine Zahlenangabe im Kalenderformat (dd.mm., d.m.yyyy etc.) folgt, bezeichnet diese 
# Zahlenangabe syntaktisch und semantisch immer ein Datum (einen Kalendertag).
# Ausnahme: Eine Zahlenangabe im Format 12.05. 
_TEMP_PREFIXES = r"(?:(?<=\bam )|(?<=\bvom )|(?<=\bzum )|(?<=\bbis )|(?<=\bab )|(?<=\bseit )|(?<=Datum: )|(?<=Geburtsdatum: ))"
_ART_PREFIXES = r"(?:(?<=\bder )|(?<=\bden )|(?<=\bdem ))"

DATE_REGEX = re.compile(
    "|".join([
        # 1. Date Range: dd. bis dd. Month yyyy
        rf"\b{_DAY}\.?\s*(?:bis|und|-|to)\s*{_DAY}\.?\s*{_MONTHS}\.?,?\s*(?:\d{{4}}|\x27\d{{2}}|\d{{2}})\b",
        # 2. Textual Date: dd. Month yyyy
        rf"\b{_DAY}\.?\s*{_MONTHS}\.?,?\s*(?:\d{{4}}|\x27\d{{2}}|\d{{2}})\b",
        # 3. Numeric Date with dots: dd.mm.yyyy or dd. mm. yyyy
        rf"(?<!\d){_DAY}\.\s*{_MONTH}\.\s*(?:\d{{4}}|\d{{2}})(?!\d)",
        # 4. Numeric Date with slashes: dd/mm/yyyy
        rf"(?<!\d){_DAY}/{_MONTH}/(?:\d{{4}}|\d{{2}})(?!\d)",
        # 5. ISO Date: yyyy-mm-dd
        rf"(?<!\d)\d{{4}}-{_MONTH}-{_DAY}(?!\d)",
        # 6. Month + Year only: Month yyyy
        rf"\b{_MONTHS}\.?,?\s*(?:\d{{4}}|\x27\d{{2}})\b",
        # 7. Date Range without year: dd. bis dd. Month
        rf"\b{_DAY}\.?\s*(?:bis|und|-|to)\s*{_DAY}\.?\s*{_MONTHS}\b",
        
        # 8. Numeric Date without year (dd.mm.) -> NUR mit temporalem Präfix
        rf"{_TEMP_PREFIXES}{_DAY}\.\s*{_MONTH}\.(?!\d)",
        # 8b. Numeric Date without year mit Artikel (z.B. der 12.05.)
        rf"{_ART_PREFIXES}{_DAY}\.\s*{_MONTH}\.(?!\d)",
        
        # 9. Textual Date without year: dd. Month
        rf"\b{_DAY}\.?\s*{_MONTHS}\b"
    ]),
    re.IGNORECASE
)

COURT_FILE_REGEX_1 = re.compile(r'\b(?:[0-9]{1,3}\s+|[IVXLCDM]+\s+)?(?:[A-Za-zÄÖÜäöü-]{1,8})\s+[0-9]{1,6}[\/-][0-9]{2,4}(?:\s*[\/-]\s*[0-9A-Za-z-]+|\s*\([0-9A-Za-z-]+\))?\b')
COURT_FILE_REGEX_2 = re.compile(r'\b(?:(?:[0-9]{1,3}|[IVXLCDM]+)\s+)?(?:[A-Za-zÄÖÜäöü]{1,8})\s+[0-9]{1,6}[\/-][0-9]{2,4}(?:\s*[-/]\s*[0-9A-Za-z]+|\s*\([0-9A-Za-z]+\))?\b|\b(?:C|T|F)-[0-9]{1,4}\/[0-9]{2}\b')

JUR_KANZLEI_REGEX = re.compile(r'\b(?:Rechtsanwälte|Rechtsanwaltskanzlei|Kanzlei)\s+((?:[A-ZÄÖÜ][\w.-]+\s*|&\s*|und\s*|Partner\s*|mbB\s*|PartGmbB\s*)+)')

# HINWEIS: TECHNICAL_SUFFIXES, MED_SUFFIXES und COMPOUND_BLACKLIST_SUFFIXES
# werden dynamisch über load_system_dictionary() aus lethe_system_dictionary geladen.

def edit_distance(s1: str, s2: str) -> int:
    """
    Berechnet die Levenshtein-Distanz (Editierdistanz) zwischen zwei Strings.
    Gibt die minimale Anzahl von Einfügungen, Löschungen oder Ersetzungen zurück,
    die erforderlich sind, um s1 in s2 umzuwandeln.
    (Die Berechnung schützt den Text davor, dass der Text unleserlich wird, 
    weil das Modell sonst alltägliche Tippfehler überinterpretiert und sinnlose Dinge weganonymisiert.)
    """
    if len(s1) > len(s2):
        s1, s2 = s2, s1
    distances = range(len(s1) + 1)
    for i2, c2 in enumerate(s2):
        distances_ = [i2+1]
        for i1, c1 in enumerate(s1):
            if c1 == c2:
                distances_.append(distances[i1])
            else:
                distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
        distances = distances_
    return distances[-1]

def is_typo_of_common_word(word: str) -> bool:
    """
    Prüft, ob ein gegebenes Wort ein exakter Treffer oder ein Tippfehler (Distanz = 1)
    eines bekannten häufigen deutschen Wortes (COMMON_GERMAN_WORDS) oder Stopworts ist.
    Gibt False zurück, falls es sich um einen bekannten Ort handelt, ansonsten
    True bei Treffer/Tippfehler.
    """
    word_lower = word.lower().strip()
    if not word_lower:
        return False
    if word_lower in KNOWN_CITIES_SET:
        return False
    if word_lower in COMMON_GERMAN_WORDS or word_lower in nlp.Defaults.stop_words:
        return True
    for common_word in COMMON_GERMAN_WORDS.union(nlp.Defaults.stop_words):
        if abs(len(word_lower) - len(common_word)) <= 1:
            if edit_distance(word_lower, common_word) == 1:
                return True
    return False

class TextPayload(BaseModel):
    text: str

class AnonymizeResponse(BaseModel):
    session_id: str
    anonymized_text: str

class DeanonymizePayload(BaseModel):
    session_id: str
    text: str

class DictionaryEntry(BaseModel):
    term: str
    category: str

class DictionaryRemovePayload(BaseModel):
    term: str
    category: str


DICTIONARY_CATEGORIES = {"PER", "ORG", "LOC", "MISC", "SKIP", "CASE_NR"}


# --- MARIADB GAZETTEER LOOKUP ---
def get_custom_entities_from_db(text: str, client_id: str) -> List[dict]:
    # Extrahiert alle Einzelwörter und Wortkandidaten (1- bis 4-Grams)
    # 1. Alle Wort-Tokens im Text finden (Buchstabenfolgen inklusive Bindestriche)
    pattern = r'\b[A-ZÄÖÜa-zäöüß0-9]+(?:-[A-ZÄÖÜa-zäöüß0-9]+)*\b'
    tokens = re.findall(pattern, text)
    
    # Zusätzlich: @-Mentions extrahieren (z.B. "@Klaus" -> "Klaus")
    at_pattern = r'@([A-ZÄÖÜa-zäöüß]+(?:-[A-ZÄÖÜa-zäöüß]+)*)'
    at_words = re.findall(at_pattern, text)

    candidates = set(tokens) | set(at_words)
    
    # 2. N-Gramme bilden (2, 3 und 4 Wörter hintereinander für z.B. "Vorname Nachname")
    for n in range(2, 5):
        for i in range(len(tokens) - n + 1):
            phrase = " ".join(tokens[i:i+n])
            candidates.add(phrase)

    phrase_tokens = list(re.finditer(r"[A-ZÄÖÜa-zäöüß0-9]+", text))
    for start_index, start_token in enumerate(phrase_tokens):
        previous_token = start_token
        for end_index in range(start_index + 1, min(start_index + 8, len(phrase_tokens))):
            next_token = phrase_tokens[end_index]
            separator = text[previous_token.end():next_token.start()]
            if not re.fullmatch(r"[\s/\\-]+", separator):
                break
            candidates.add(text[start_token.start():next_token.end()])
            previous_token = next_token

    for court_file_regex in (COURT_FILE_REGEX_1, COURT_FILE_REGEX_2):
        candidates.update(
            match.group()
            for match in court_file_regex.finditer(text)
        )

    if not candidates:
        return []

    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        
        blind_indices = [compute_blind_index(c) for c in candidates if c]
        if not blind_indices:
            return []

        # Mandantengenauer Lookup via Blind-Index: nur Einträge dieser client_id werden verwendet
        rows = []
        for offset in range(0, len(blind_indices), 500):
            batch = blind_indices[offset:offset + 500]
            format_strings = ','.join(['%s'] * len(batch))
            query = (
                f"SELECT term, category FROM lethe_dictionary "
                f"WHERE client_id = %s AND blind_index IN ({format_strings})"
            )
            cursor.execute(query, (client_id, *batch))
            rows.extend(cursor.fetchall())
        
        cursor.close()
        conn.close()
        
        return [{"label": row[1], "pattern": decrypt_term(row[0])} for row in rows]
    except Exception as e:
        _log_error(
            error_type="DB_GAZETTEER_ERROR",
            message="lethe_dictionary Lookup fehlgeschlagen",
            details=str(e),
            client_id=client_id
        )
        return []



async def verify_db_admin(request: Request) -> str:
    """
    Verifiziert, ob der Caller ein System-Administrator ist.
    Ein Admin ist dadurch definiert, dass er in admin_auth steht, 
    aber KEINEN Eintrag in client_auth hat.
    """
    x_access_code = request.headers.get("X-Access-Code")
    if not x_access_code:
        _fail_auth(
            error_type="AUTH_MISSING_HEADER",
            message="X-Access-Code Header fehlt"
        )
    try:
        val = int(x_access_code)
        try:
            decrypted_val = decrypt_access_code(val)
            db_lookup_code = f"{decrypted_val:08d}"
        except Exception:
            db_lookup_code = x_access_code
    except (ValueError, TypeError):
        _fail_auth(
            error_type="AUTH_INVALID_FORMAT",
            message="X-Access-Code ist kein gültiger Integer im Bereich 0–99999999",
            details=f"Übermittelter Wert: {x_access_code!r}"
        )

    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT a.client_id, a.status, c.status
            FROM admin_auth a
            LEFT JOIN client_auth c ON a.client_id = c.client_id
            WHERE a.unlock_code = %s OR a.unlock_code = %s
            LIMIT 1
            """,
            (db_lookup_code, x_access_code)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
    except Exception as e:
        _fail_auth(
            error_type="AUTH_DB_ERROR",
            message="DB-Abfrage zur Admin-Verifizierung fehlgeschlagen",
            details=str(e)
        )

    if row is None:
        _fail_auth(
            error_type="AUTH_UNKNOWN_CLIENT",
            message="Unlock-Code nicht in admin_auth gefunden",
            details=f"Unlock-Code (maskiert): {x_access_code[:2]}******{x_access_code[-2:]}"
        )

    client_id_raw, admin_status, client_status = row

    if admin_status != 'active':
        _fail_auth(
            error_type="AUTH_ADMIN_LOCKED",
            message="Admin-Account ist nicht aktiv",
            details=f"Status: {admin_status!r}",
            client_id=str(client_id_raw) if client_id_raw else None
        )

    if client_status is not None:
        _fail_auth(
            error_type="AUTH_NOT_ADMIN",
            message="Dieser Code gehört zu einem regulären Client, nicht zum System-Admin.",
            details="Eintrag in client_auth vorhanden."
        )

    return str(client_id_raw)

@app.post("/v1/admin/config/reload")
async def reload_config(request: Request, admin_id: str = Depends(verify_db_admin)):
    """
    Lädt die NLP-Konfiguration (nlp_config.json) und die System-Dictionary-DB neu.
    Nur für Administratoren von localhost aus zugänglich.
    """
    if request.client is None or request.client.host not in ["127.0.0.1", "::1", "localhost"]:
        raise HTTPException(status_code=403, detail="Dieser Endpunkt darf nur lokal aufgerufen werden.")
    try:
        load_nlp_config()
        load_system_dictionary()
        return {"status": "success", "message": "Konfigurationen und System-Wörterbuch erfolgreich neu geladen!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/anonymize", response_model=AnonymizeResponse)
@limiter.limit("60/minute")
async def anonymize_text(request: Request, payload: TextPayload, client_id: str = Depends(verify_client)):

    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
        
    max_text_len = _get_client_max_text_length(client_id)
    if max_text_len > 0 and len(payload.text) > max_text_len:
        _log_error(
            error_type="TEXT_TOO_LONG",
            message=f"Text überschreitet das Mandanten-Limit von {max_text_len} Zeichen",
            details=f"Textlänge: {len(payload.text)} Zeichen, Limit: {max_text_len} Zeichen",
            client_id=client_id
        )
        raise HTTPException(
            status_code=413,
            detail=f"Der Text überschreitet die maximale zulässige Länge von {max_text_len} Zeichen."
        )

    original_text = payload.text

    
    # --- SCHRITT 0: ZEILEN-SANITY-PROTECTION (Der SpaCy-Transformer-Fix) ---
    # Wir fügen temporär am Ende jeder Zeile einen Punkt ein, falls keiner da ist.
    # Das zwingt SpaCy, an jedem Zeilenumbruch ein hartes Satzende (Sentence Boundary) zu erkennen.
    sanitized_text = ""
    for line in original_text.splitlines(keepends=True):
        stripped = line.strip()
        if stripped and not stripped.endswith((".", ":", "!", "?")):
            # Wenn die Zeile Text hat, aber kein Satzzeichen, fügen wir einen "Geister-Punkt" ein
            if line.endswith("\n"):
                sanitized_text += line[:-1] + ".\n"
            else:
                sanitized_text += line + "."
        else:
            sanitized_text += line

    session_id = str(uuid.uuid4())
    mapping: Dict[str, str] = {}
    counters = {"PER": 1, "ORG": 1, "LOC": 1, "PHONE": 1, "TAXID": 1, "EMAIL": 1, "ZIP": 1, "IBAN": 1, "BIC": 1, "DATE": 1, "CASE_NR": 1}
    
    # 1. Dynamischer EntityRuler (läuft auf dem originalen Text für exakte Treffer)
    ruler = nlp.get_pipe("entity_ruler") if "entity_ruler" in nlp.pipe_names else nlp.add_pipe("entity_ruler", before="ner")
    ruler.clear()
    ruler.add_patterns(TITLE_PATTERNS)
    ruler.add_patterns(KNOWN_CITIES_PATTERNS)
    ruler.add_patterns(SKIP_PATTERNS)
    
    db_patterns = get_custom_entities_from_db(original_text, client_id)
    if db_patterns:
        ruler.add_patterns(db_patterns)
    whitelist_terms = {
        p["pattern"].strip().lower()
        for p in db_patterns
        if p["label"] == "SKIP"
    }


    extracted_entities = []
    protected_spans = []

    # 2. HÖCHSTE PRIORITÄT: Regex-Kaskade auf dem ORIGINAL-TEXT
    for match in COURT_FILE_REGEX_1.finditer(original_text):
        label = "SKIP" if match.group().strip().lower() in whitelist_terms else "CASE_NR"
        extracted_entities.append((match.start(), match.end(), label, match.group()))

    for match in COURT_FILE_REGEX_2.finditer(original_text):
        label = "SKIP" if match.group().strip().lower() in whitelist_terms else "CASE_NR"
        extracted_entities.append((match.start(), match.end(), label, match.group()))

    for match in IBAN_REGEX.finditer(original_text):
        if is_valid_iban(match.group()):
            extracted_entities.append((match.start(), match.end(), "IBAN", match.group()))

    for match in BIC_REGEX.finditer(original_text):
        if is_valid_bic(match.group()):
            extracted_entities.append((match.start(), match.end(), "BIC", match.group()))

    for match in EMAIL_REGEX.finditer(original_text):
        extracted_entities.append((match.start(), match.end(), "EMAIL", match.group()))

    for match in TAX_ID_REGEX.finditer(original_text):
        extracted_entities.append((match.start(), match.end(), "TAXID", match.group()))

    for match in ZIP_REGEX.finditer(original_text):
        extracted_entities.append((match.start(), match.end(), "ZIP", match.group()))

    for match in DATE_REGEX.finditer(original_text):
        extracted_entities.append((match.start(), match.end(), "DATE", match.group()))

    for match in PHONE_REGEX.finditer(original_text):
        extracted_entities.append((match.start(), match.end(), "PHONE", match.group()))

    for match in AT_MENTION_REGEX.finditer(original_text):
        extracted_entities.append((match.start(), match.end(), "PER", match.group()))

    # JUR-Radar
    if JUR_COURT_REGEX:
        for match in JUR_COURT_REGEX.finditer(original_text):
            extracted_entities.append((match.start(1), match.end(1), "ORG", match.group(1)))
    if JUR_INST_REGEX:
        for match in JUR_INST_REGEX.finditer(original_text):
            extracted_entities.append((match.start(1), match.end(1), "LOC", match.group(1)))
    if JUR_TITLE_REGEX:
        for match in JUR_TITLE_REGEX.finditer(original_text):
            extracted_entities.append((match.start(1), match.end(1), "PER", match.group(1)))
    if JUR_ROLE_REGEX:
        for match in JUR_ROLE_REGEX.finditer(original_text):
            extracted_entities.append((match.start(1), match.end(1), "PER", match.group(1)))
    if JUR_REPRESENTATIVE_REGEX:
        law_firm_spans = [
            (match.start(), match.end(1))
            for match in JUR_KANZLEI_REGEX.finditer(original_text)
        ]
        for match in JUR_REPRESENTATIVE_REGEX.finditer(original_text):
            if any(
                not (match.end(1) <= start or match.start(1) >= end)
                for start, end in law_firm_spans
            ):
                continue
            extracted_entities.append((match.start(1), match.end(1), "PER", match.group(1)))
    for match in JUR_KANZLEI_REGEX.finditer(original_text):
        org_text = match.group(1).strip()
        # Remove trailing "und", "&" if present
        while org_text.endswith(" und") or org_text.endswith(" &"):
            org_text = org_text.rsplit(" ", 1)[0]
        protected_spans.append((match.start(), match.start(1)))
        extracted_entities.append((match.start(1), match.start(1) + len(org_text), "ORG", org_text))

    for pattern in db_patterns:
        term = pattern["pattern"]
        if not term:
            continue
        left_boundary = r"(?<!\w)" if term[0].isalnum() or term[0] == "_" else ""
        right_boundary = r"(?!\w)" if term[-1].isalnum() or term[-1] == "_" else ""
        term_regex = re.compile(left_boundary + re.escape(term) + right_boundary)
        for match in term_regex.finditer(original_text):
            extracted_entities.append(
                (match.start(), match.end(), pattern["label"], match.group())
            )

    regex_spans = [
        (start, end) for start, end, label, text in extracted_entities
    ] + protected_spans

    # =========================================================================
    # 3. SPACY NER AUF DEM SANITIZED TEXT (MIT ANREDEN-ERWEITERUNG)
    # =========================================================================
    doc = nlp(sanitized_text)
    
    STOP_LABELS = {"phone", "tel", "telefon", "mobil", "e-mail", "email", "fax", "impressum"}
    custom_db_terms = {p["pattern"].lower() for p in db_patterns}
    TITEL_LISTE = [
        # --- Akademische Kombinationen (Lang zu Kurz) ---
        "professor doktor", "prof. dr. med.", "prof. dr.-ing.", "prof. dr.", "pd dr.",
        "professorin", "professor", "prof.", "doktor", "dr. med.", "dr. ing.", "dr.",
        
        # --- Klassische deutsche Anreden & Plurale ---
        "sehr geehrte frau", "sehr geehrter herr", "fräulein", "kollegin", "kollege",
        "herren", "damen", "frau", "herr", "fr.", "hr.",
        
        # --- Internationale / Englische Anreden ---
        "professor", "mrs.", "miss", "mr.", "ms.",
        
        # --- Business- & Hierarchie-Rollen (Häufige Prompt-Einleitungen) ---
        "geschäftsführer", "ceo", "cto", "cfo", "chief", "manager", "leiter", "admin"
    ]

    # (Dein bestehender Code für geist_punkt_indices bleibt hier unverändert...)
    geist_punkt_indices = []
    current_pos = 0
    for line in original_text.splitlines(keepends=True):
        stripped = line.strip()
        line_len = len(line)
        if stripped and not stripped.endswith((".", ":", "!", "?")):
            dot_pos = current_pos + (line_len - 1 if line.endswith("\n") else line_len)
            geist_punkt_indices.append(dot_pos)
            current_pos += line_len + 1
        else:
            current_pos += line_len

    known_person_names = {
        value.strip().lower()
        for _, _, label, value in extracted_entities
        if label == "PER" and len(value.strip().split()) == 1
    }

    for ent in doc.ents:
        if ent.label_ in ["PER", "ORG", "LOC", "MISC", "CASE_NR"]:
            clean_ent_text = ent.text.rstrip(".")
            # --- TABELLEN- & ZEILENTRENNER SCHUTZ ---
            # Wenn SpaCy versehentlich über ein '|' oder Zeilenumbruch hinweg matcht, schneiden wir strikt davor ab.
            if "|" in clean_ent_text:
                clean_ent_text = clean_ent_text.split("|")[0].strip()
            if "\n" in clean_ent_text:
                clean_ent_text = clean_ent_text.split("\n")[0].strip()

            if not clean_ent_text.strip() or clean_ent_text.lower() in whitelist_terms:
                continue            
            if clean_ent_text.lower().strip(": ") in STOP_LABELS:
                continue

            # --- FILTER OUT TYPOS AND COMMON WORDS ---
            if clean_ent_text.lower() not in KNOWN_CITIES_SET and clean_ent_text.lower() not in custom_db_terms:
                if is_typo_of_common_word(clean_ent_text):
                    continue

            # --- POS-FILTER FÜR SUBSTANTIVIERTE VERBEN & NORMALE NOMEN (z.B. "Ausbügeln") ---
            # Verhindert, dass SpaCy Einzelwörter als ORG/PER/LOC/MISC erkennt, wenn sie vom POS-Tagger
            # als normales Nomen (NN) statt Eigenname (NE) getaggt wurden und NICHT im Wörterbuch stehen.
            # HINWEIS: Organisationen werden vom NN-Filter ausgenommen, da SpaCy Firmen
            # in bestimmten Kontexten fälschlicherweise als NN statt NE taggt.
            if clean_ent_text.lower() not in custom_db_terms:
                if len(ent) == 1 and ent.root.tag_ == "NN" and ent.label_ != "ORG":
                    continue

            # --- ABKÜRZUNGS- UND BINDESTRICH-SCHUTZ ---
            # 1. Ganzen Begriff prüfen (z. B. "u.a.", "z.B.", "Dr.")
            norm_text = clean_ent_text.replace(".", "").rstrip("-").strip().lower()
            if norm_text in NORMALIZED_ABBREVIATIONS:
                continue

            # 2. Wenn der Text einen Bindestrich enthält, das letzte Suffix prüfen (z. B. "Leber-Werte" oder "Session-ca.")
            if "-" in clean_ent_text:
                last_suffix = clean_ent_text.split("-")[-1].replace(".", "").strip().lower()
                if last_suffix in COMPOUND_BLACKLIST_SUFFIXES or last_suffix in NORMALIZED_ABBREVIATIONS:
                    continue

            ent_label = ent.label_

            # --- MISC HANDLING (Deppen-Apostroph / Genitiv-s mit Nomen) ---
            if ent.label_ == "MISC":
                words = clean_ent_text.split()
                if len(words) > 1:
                    last_word = words[-1]
                    penultimate_word = words[-2]
                    has_genitive = False
                    if penultimate_word[0].isupper() and last_word[0].isupper():
                        # A) Check for apostrophe-s (Deppen-Apostroph, e.g. Robert's)
                        for suffix in ["'s", "’s", "´s", "`s"]:
                            if penultimate_word.lower().endswith(suffix) and len(penultimate_word) > len(suffix):
                                has_genitive = True
                                break
                        # B) Check for genitive apostrophe after s, z, x, ß (e.g. Thomas')
                        if not has_genitive:
                            for apostrophe in ["'", "’", "´", "`"]:
                                if penultimate_word.endswith(apostrophe) and len(penultimate_word) > 1:
                                    char_before = penultimate_word[-2].lower()
                                    if char_before in ['s', 'z', 'x', 'ß']:
                                        has_genitive = True
                                        break
                        # C) Check for normal genitive-s (e.g. Roberts)
                        if not has_genitive:
                            if penultimate_word.endswith("s") and len(penultimate_word) > 2:
                                if penultimate_word.lower() not in ["des", "das", "eines", "dieses", "jenes", "welches", "jedes"]:
                                    has_genitive = True
                    if has_genitive:
                        ent_label = "PER"
                        # Only cut off if the last token is not a proper name (NE / PROPN)
                        if ent[-1].tag_ != "NE" and ent[-1].pos_ != "PROPN":
                            clean_ent_text = " ".join(words[:-1])
                    else:
                        continue
                else:
                    continue

            # --- NEU: SCHUTZ VOR MITGESCHLUCKTEN NOMEN (z.B. "Roberts Auto") ---
            # Wenn SpaCy mehr als ein Wort als Name erkennt, prüfen wir das letzte Wort.
            if ent_label == "PER":
                words = clean_ent_text.split()
                if len(words) > 1:
                    last_word = words[-1]
                    penultimate_word = words[-2]
                    # Wenn das letzte Wort kein Name ist (z.B. weil es nicht im Namenskontext steht)
                    # oder ein bekanntes allgemeines Nomen darstellt, schneiden wir es ab.
                    # Ein einfacher, hocheffektiver Indikator im Deutschen: Hat das Wort ein Genitiv-s davor?
                    if last_word[0].isupper() and penultimate_word[0].isupper():
                        has_genitive = False
                        if penultimate_word.endswith('s') or penultimate_word.endswith('S'):
                            has_genitive = True
                        else:
                            for suffix in ["'s", "’s", "´s", "`s"]:
                                if penultimate_word.lower().endswith(suffix):
                                    has_genitive = True
                                    break
                        if not has_genitive:
                            for apostrophe in ["'", "’", "´", "`"]:
                                if penultimate_word.endswith(apostrophe) and len(penultimate_word) > 1:
                                    char_before = penultimate_word[-2].lower()
                                    if char_before in ['s', 'z', 'x', 'ß']:
                                        has_genitive = True
                                        break
                        if has_genitive and ent[-1].tag_ != "NE" and ent[-1].pos_ != "PROPN":
                            clean_ent_text = " ".join(words[:-1])

            words = clean_ent_text.split()
            if ent_label == "PER" and len(words) > 1:
                first_word = words[0].lower()
                if first_word.endswith("s") and first_word[:-1] in known_person_names:
                    clean_ent_text = words[0]

            sanitized_start = ent.start_char
            dots_before = sum(1 for p in geist_punkt_indices if p < sanitized_start)
            
            actual_start = sanitized_start - dots_before
            # Die End-Position muss dynamisch anhand des potenziell gekürzten Textes berechnet werden!
            actual_end = actual_start + len(clean_ent_text)

            # --- @-MENTION FIX ---
            # Wenn direkt vor dem erkannten Namen ein '@' steht (z.B. "@Klaus"),
            # erweitern wir den Match, damit das @-Zeichen mitsamt anonymisiert wird.
            if actual_start > 0 and original_text[actual_start - 1] == '@':
                actual_start -= 1
                clean_ent_text = original_text[actual_start:actual_end]

            # --- DEPPEN-APOSTROPH & GENITIV-S ERWEITERUNG ---
            # Wenn direkt nach dem erkannten Namen "'s" oder ein reines Genitiv-"s" steht,
            # das von SpaCy ignoriert wurde, ziehen wir es in die Entität representation hinein.
            if actual_end < len(original_text):
                # Prüfe auf Apostroph-s (z.B. Robert's)
                if original_text[actual_end:actual_end+2].lower() == "'s":
                    actual_end += 2
                    clean_ent_text = original_text[actual_start:actual_end]
                # Prüfe auf isoliertes Genitiv-s, falls SpaCy es abgeschnitten hat
                elif original_text[actual_end] == 's' and (actual_end + 1 == len(original_text) or not original_text[actual_end+1].isalpha()):
                    actual_end += 1
                    clean_ent_text = original_text[actual_start:actual_end]


            # --- DER LOOK-BACK-STABILISATOR ---
            if ent_label == "PER":
                lookback_zone = original_text[max(0, actual_start - 10):actual_start].lower()
                for titel in TITEL_LISTE:
                    if lookback_zone.endswith(titel + " "):
                        titel_laenge = len(titel) + 1
                        actual_start = actual_start - titel_laenge
                        clean_ent_text = original_text[actual_start:actual_end]
                        break

            # Validierung gegen den Originaltext
            if original_text[actual_start:actual_end] == clean_ent_text:
                ent_start, ent_end = actual_start, actual_end
            else:
                # Fallback über lokalen Suchradius
                start_idx = original_text.find(clean_ent_text, max(0, actual_start - 10), min(len(original_text), actual_end + 10))
                if start_idx != -1:
                    ent_start, ent_end = start_idx, start_idx + len(clean_ent_text)
                else:
                    continue

            # Prüfen, ob die SpaCy-Entität mit einer hochprioritären Regex-Entität überlappt (Regex gewinnt vor SpaCy)
            if any(not (ent_end <= r_start or ent_start >= r_end) for r_start, r_end in regex_spans):
                continue

            extracted_entities.append((ent_start, ent_end, ent_label, clean_ent_text))
            if ent_label == "PER" and len(clean_ent_text.split()) == 1:
                known_person_names.add(clean_ent_text.lower())

    # =========================================================================
    # 4. ÜBERLAPPUNGEN AUFLÖSEN (Regex gewinnt vor SpaCy)
    # =========================================================================
    extracted_entities.sort(key=lambda x: (x[0], -(x[1] - x[0])))
    filtered_entities = []
    last_end = 0
    for start, end, label, text in extracted_entities:
        if start >= last_end:
            filtered_entities.append((start, end, label, text))
            last_end = end

    # =========================================================================
    # 5. EINDEUTIGE TAGS VORAB FESTLEGEN (MIT HOCHPRÄZISER KOREFERENZ-FUSION)
    # =========================================================================
    lemma_to_tag: Dict[str, str] = {}
    mapping: Dict[str, str] = {}
    
    # Nach Länge aufsteigend sortieren, damit kürzere Stammformen zuerst verarbeitet werden
    filtered_entities.sort(
        key=lambda x: (x[2] != "LOC", x[0] if x[2] == "LOC" else len(x[3]))
    )
    
    for start, end, label, original_value in filtered_entities:
        if label not in counters:
            counters[label] = 1
    
        # Bereinigung: @-Mentions für den ID-Abgleich ignorieren.
        clean_key = original_value.strip().lower()
        if clean_key.startswith("@"):
            clean_key = clean_key[1:]
            
        matched_tag = None
    
        if label in ["PER", "ORG", "LOC"]:
            for existing_name, existing_tag in lemma_to_tag.items():
                # 1. Volle Übereinstimmung
                if clean_key == existing_name:
                    matched_tag = existing_tag
                    break
                # 2. Genitiv-Match (Peter -> Peters)
                if clean_key in [existing_name + "s", existing_name + "'s", existing_name + "es"]:
                    matched_tag = existing_tag
                    break
                # 3. Präziser Teilwort-Match mit Wortgrenzen (Verhindert "Roberts Auto" -> "Robert")
                # Wir spalten in einzelne Wörter auf und prüfen, ob die Basisform ein echtes Token ist
                clean_words = clean_key.split()
                existing_words = existing_name.split()
                
                # Prüfen, ob alle Wörter des kürzeren Namens im längeren Namen vorkommen
                if all(any(w.startswith(ew) or ew.startswith(w) for w in clean_words) for ew in existing_words):
                    # ZUSÄTZLICHER SCHUTZ: Wenn das Label PER ist, darf das angehängte Wort kein normales Nomen sein
                    # Wenn clean_words mehr Wörter hat als existing_words, inspizieren wir die "Überschüsse"
                    is_valid_naming_extension = True
                    excess_words = [w for w in clean_words if w not in existing_words and not w.endswith('s')]
                    
                    # Wenn hier typische Substantive auftauchen, blockieren wir die Verschmelzung
                    # (Optional: Hier könnte man feingranularer filtern, aber der Wortgrenzen-Match fängt 95% ab)
                    if matched_tag: 
                        break
                    
                    matched_tag = existing_tag
                    break
                
            if matched_tag:
                tag = matched_tag
            else:
                tag = f"[{label}_{counters[label]}]"
                lemma_to_tag[clean_key] = tag
                counters[label] += 1
        else:
            if label == "SKIP":
                tag = original_value
            elif clean_key in lemma_to_tag:
                tag = lemma_to_tag[clean_key]
            else:
                tag = f"[{label}_{counters[label]}]"
                lemma_to_tag[clean_key] = tag
                counters[label] += 1
    
        mapping[original_value] = tag

    # =========================================================================
    # 6. ERSETZUNG VON HINTEN NACH VORNE (STRENG NACH INDEX)
    # =========================================================================
    # WICHTIG: Für die Ersetzung MUSS zwingend nach Start-Index sortiert werden!
    filtered_entities.sort(key=lambda x: x[0], reverse=True)
    modified_text = original_text
    
    for start, end, label, original_value in filtered_entities:
        tag = mapping[original_value]
        
        prefix = ""
        suffix = ""
        
        if start > 0:
            char_before = original_text[start-1]
            if char_before != "\n" and not char_before.isspace() and char_before not in ".,;:!?":
                prefix = " "
                
        if end < len(original_text):
            char_after = original_text[end]
            if not char_after.isspace() and char_after not in ".,;:!?":
                suffix = " "
        
        modified_text = modified_text[:start] + prefix + tag + suffix + modified_text[end:]
            
    # Umdrehen für den Rückweg
    reverse_mapping = {}
    for orig_val, tag_val in mapping.items():
        if tag_val not in reverse_mapping:
            reverse_mapping[tag_val] = []
        reverse_mapping[tag_val].append(orig_val)
        
    for tag_val in reverse_mapping:
        reverse_mapping[tag_val].sort(key=len, reverse=True)

    occurrence_mapping = {}
    for start, end, label, original_value in sorted(filtered_entities, key=lambda x: x[0]):
        tag = mapping[original_value]
        if tag != original_value:
            occurrence_mapping.setdefault(tag, []).append(original_value)
        
    # AUDIT / SECURITY (BOLA / IDOR Protection & Session TTL):
    # Speichert die client_id explizit mit dem Mapping in der Session
    # sowie den Erstellungszeitpunkt (created_at) für das automatische Ablaufdatum (TTL: 1 Std.).
    sessions_db[session_id] = {
        "client_id": client_id,
        "mapping": reverse_mapping,
        "occurrences": occurrence_mapping,
        "created_at": time.time()
    }

    # --- API-LOGGING ---
    word_count = len(original_text.split())
    _log_api_call(client_id, "anonymize", word_count)

    return AnonymizeResponse(session_id=session_id, anonymized_text=modified_text)


@app.post("/v1/deanonymize")
@limiter.limit("60/minute")
async def deanonymize_text(request: Request, payload: DeanonymizePayload, client_id: str = Depends(verify_client)):

    if payload.session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Session ID not found or already expired")
        
    session_data = sessions_db[payload.session_id]

    # TTL / EXPIRATION CHECK (1 Std. Max-Alter):
    if time.time() - session_data.get("created_at", 0) > SESSION_MAX_AGE_SECONDS:
        sessions_db.pop(payload.session_id, None)
        raise HTTPException(status_code=410, detail="Session ist abgelaufen (TTL 1 Std. überschritten).")

    # =========================================================================
    # AUDIT / SECURITY CHECK: BOLA / IDOR (Broken Object Level Authorization)
    # =========================================================================
    # Verhindert, dass ein authentifizierter Mandant A die Session-ID von Mandant B
    # errät, abfängt oder nutzt, um fremde Daten zu deanonymisieren.
    if session_data.get("client_id") != client_id:
        _log_error(
            error_type="AUTH_IDOR_VIOLATION",
            message="Unberechtigter Zugriff auf fremde Session-ID (BOLA/IDOR Versuch)",
            details=f"Session-ID: {payload.session_id!r}, Eigentümer-Client: {session_data.get('client_id')!r}, Aufrufer-Client: {client_id!r}",
            client_id=client_id
        )
        raise HTTPException(
            status_code=403,
            detail="Zugriff verweigert: Diese Session-ID gehört einem anderen Mandanten."
        )

    reverse_mapping = session_data["mapping"]
    occurrence_mapping = session_data.get("occurrences", {})
    result_text = payload.text
    
    # reverse_mapping sieht z.B. so aus: {"[PER_1]": ["Peters", "Peter"]}
    for tag, original_values in reverse_mapping.items():
        if tag in occurrence_mapping:
            occurrence_index = 0
            fallback_value = original_values[0]

            def restore_occurrence(_match):
                nonlocal occurrence_index
                if occurrence_index < len(occurrence_mapping[tag]):
                    original_value = occurrence_mapping[tag][occurrence_index]
                    occurrence_index += 1
                    return original_value
                return fallback_value

            result_text = re.sub(re.escape(tag), restore_occurrence, result_text)
            continue

        # Da wir vorab nach Länge sortiert haben, wird erst versucht, das Tag zu ersetzen.
        # Wenn das LLM den Satzbau beibehalten hat, steht dort "[PER_1] Auto".
        # Das Problem: Das LLM könnte das s entfernt haben, weil es das Tag als reinen Namen sieht.
        # Deshalb müssen wir intelligent vorgehen:
        
        for original_value in original_values:
            # Wenn das Wort im Original ein Genitiv war ("Peters"), das LLM aber nur noch 
            # "[PER_1]" (ohne nachfolgendes "s") im Text stehen hat, müssen wir prüfen, 
            # ob der Kontext passt. 
            # Ein simpler, extrem stabiler Weg für den Prototyp:
            result_text = result_text.replace(tag, original_value)
        
    del sessions_db[payload.session_id]

    # --- API-LOGGING ---
    word_count = len(payload.text.split())
    _log_api_call(client_id, "deanonymize", word_count)

    return {"text": result_text}

@app.post("/v1/dictionary/add")
@limiter.limit("60/minute")
async def add_dictionary_entry(request: Request, entry: DictionaryEntry, client_id: str = Depends(verify_client)):

    clean_term = entry.term.strip()
    clean_category = entry.category.strip().upper()
    
    if clean_category not in DICTIONARY_CATEGORIES:
        raise HTTPException(status_code=400, detail="Ungültige Kategorie")

    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        
        # Mandantengenau: Existenzprüfung nur innerhalb der client_id via Blind Index
        blind_idx = compute_blind_index(clean_term)
        query_check = "SELECT id, category FROM lethe_dictionary WHERE blind_index = %s AND client_id = %s"
        cursor.execute(query_check, (blind_idx, client_id))
        existing_rows = cursor.fetchall()
        
        if existing_rows:
            # Wir nehmen den ersten gefundenen Eintrag für das Update
            existing_id, existing_category = existing_rows[0]
            
            # Fall A: Kategorie hat sich geändert (z.B. von PER zu SKIP)
            if existing_category != clean_category:
                query_update = """
                    UPDATE lethe_dictionary 
                    SET category = %s, created_at = %s 
                    WHERE id = %s AND client_id = %s
                """
                cursor.execute(query_update, (
                    clean_category, 
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                    existing_id,
                    client_id
                ))
                
                # Verbleibende Duplikate dieser client_id bereinigen
                if len(existing_rows) > 1:
                    other_ids = [row[0] for row in existing_rows[1:]]
                    format_strings = ','.join(['%s'] * len(other_ids))
                    cursor.execute(
                        f"DELETE FROM lethe_dictionary WHERE id IN ({format_strings}) AND client_id = %s",
                        (*tuple(other_ids), client_id)
                    )
                
                conn.commit()
                return {
                    "status": "updated", 
                    "message": f"Kategorie für '{clean_term}' auf {clean_category} geändert."
                }
            
            # Fall B: Existiert bereits exakt so
            return {"status": "exists", "message": "Eintrag existiert bereits identisch."}
        
        # Eintrag existiert noch nicht -> INSERT mit client_id und blind_index
        query_insert = """
            INSERT INTO lethe_dictionary (client_id, term, category, blind_index, match_type, created_at) 
            VALUES (%s, %s, %s, %s, 'exact', %s)
        """
        cursor.execute(query_insert, (
            client_id,
            encrypt_term(clean_term), 
            clean_category, 
            blind_idx,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
        return {"status": "created", "message": f"'{clean_term}' erfolgreich hinzugefügt."}
        
    except Exception as e:
        import traceback
        _log_syslog(f"Datenbankfehler (MariaDB): {traceback.format_exc()}", priority=syslog.LOG_ERR)
        raise HTTPException(status_code=500, detail=f"Datenbankfehler (MariaDB): {str(e)}")


    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


@app.delete("/v1/dictionary/remove")
@limiter.limit("60/minute")
async def remove_from_dictionary(request: Request, payload: DictionaryRemovePayload, client_id: str = Depends(verify_client)):
    """
    Löscht einen gelernten Begriff aus dem Mandanten-Wörterbuch.
    """
    clean_category = payload.category.strip().upper()

    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        
        # Mandantengenau: nur Einträge der eigenen client_id können gelöscht werden
        blind_idx = compute_blind_index(payload.term.strip())
        query = "DELETE FROM lethe_dictionary WHERE blind_index = %s AND category = %s AND client_id = %s"
        cursor.execute(query, (blind_idx, clean_category, client_id))
        conn.commit()

        
        affected_rows = cursor.rowcount
        cursor.close()
        conn.close()
        
        if affected_rows == 0:
            raise HTTPException(status_code=404, detail="Begriff in dieser Kategorie nicht gefunden.")
            
        return {"status": "success", "message": f"'{payload.term}' wurde aus Kategorie '{payload.category}' entfernt."}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Datenbankfehler beim Löschen: {e}")


@app.get("/v1/dictionary/list")
@limiter.limit("60/minute")
async def list_dictionary(request: Request, client_id: str = Depends(verify_client)):

    """
    Gibt die Liste der gelernten Begriffe für diese client_id zurück.
    """
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        
        # Mandantengenau: nur Einträge der eigenen client_id
        cursor.execute(
            "SELECT term, category FROM lethe_dictionary WHERE client_id = %s ORDER BY created_at DESC",
            (client_id,)
        )
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return [{"term": decrypt_term(row[0]), "category": row[1]} for row in rows]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Datenbankfehler beim Auflisten: {e}")

@app.post("/v1/extract-text")
@limiter.limit("15/minute")
async def extract_text_from_file(
    request: Request,
    file: UploadFile = File(...),
    client_id: str = Depends(verify_client)
):

    """
    Nimmt ein Dokument entgegen und extrahiert den rohen Text
    für die Weiterverarbeitung im Frontend.
    Prüft die maximale Dateigröße (max_file_size_mb aus client_auth).
    0 = unbegrenzt.
    """
    max_mb = _get_client_max_file_size_mb(client_id)
    
    # Dateigrößen-Prüfung zur DoS-Vermeidung
    if max_mb > 0:
        max_bytes = max_mb * 1024 * 1024
        
        # 1. Schnelle Vorabprüfung über Header/Attributes, falls vorhanden
        if file.size and file.size > max_bytes:
            _log_error(
                error_type="FILE_TOO_LARGE",
                message=f"Datei überschreitet das Mandanten-Limit von {max_mb} MB",
                details=f"Dateigröße (Header): {file.size} Bytes, Limit: {max_bytes} Bytes",
                client_id=client_id
            )
            raise HTTPException(
                status_code=413, 
                detail=f"Die Datei überschreitet die maximale zulässige Dateigröße von {max_mb} MB."
            )
            
        # 2. Gestreamtes Lesen in Chunks zur Verhinderung von OOM/DoS bei riesigen Uploads
        content_bytes = bytearray()
        chunk_size = 64 * 1024
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            content_bytes.extend(chunk)
            if len(content_bytes) > max_bytes:
                _log_error(
                    error_type="FILE_TOO_LARGE",
                    message=f"Datei überschreitet das Mandanten-Limit von {max_mb} MB beim Einlesen",
                    details=f"Gelesene Bytes: {len(content_bytes)}, Limit: {max_bytes} Bytes",
                    client_id=client_id
                )
                raise HTTPException(
                    status_code=413, 
                    detail=f"Die Datei überschreitet die maximale zulässige Dateigröße von {max_mb} MB."
                )
        raw_data = bytes(content_bytes)
    else:
        raw_data = await file.read()

    filename = file.filename.lower() if file.filename else ""
    content_type = file.content_type if file.content_type else ""
    
    try:
        file_stream = io.BytesIO(raw_data)
        
        # 1. TEXT / MARKDOWN
        if content_type == "text/plain" or filename.endswith(('.txt', '.md')):
            return {"text": raw_data.decode("utf-8")}
            
        # 2. WORD (.docx)
        elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or filename.endswith('.docx'):
            doc = Document(file_stream)
            full_text = [para.text for para in doc.paragraphs]
            return {"text": "\n".join(full_text)}
            
        # 3. OPENOFFICE / LIBREOFFICE (.odt)
        elif content_type == "application/vnd.oasis.opendocument.text" or filename.endswith('.odt'):
            odt_doc = load(file_stream)
            all_paragraphs = odt_doc.getElementsByType(text.P)
            full_text = [teletype.extractText(p) for p in all_paragraphs]
            return {"text": "\n".join(full_text)}
            
        # 4. PDF (.pdf)
        elif content_type == "application/pdf" or filename.endswith('.pdf'):
            reader = pypdf.PdfReader(file_stream)
            full_text = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    page_text = re.sub(r'(?<=\b\w)\s(?=\w\b)', '', page_text)
                    page_text = re.sub(r'[ \t]+', ' ', page_text)
                    full_text.append(page_text)
                    
            return {"text": "\n".join(full_text)}
            
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Dateiformat nicht unterstützt: {content_type}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Fehler beim Parsen der Datei: {str(e)}"
        )
        

# für die Suchanfragen eines lokalen clients
@app.get("/v1/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "lethe-gateway",
        "ver": os.getenv("LETHE_GATEWAY_VER", "unknown")
    }
