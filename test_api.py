from dataclasses import dataclass
import json
import re
import ssl
import sys
from typing import List, Optional
import urllib.error
import urllib.request

BASE_URL = "https://localhost:8000/v1"
ANONYMIZE_URL = f"{BASE_URL}/anonymize"
DEANONYMIZE_URL = f"{BASE_URL}/deanonymize"
ACCESS_CODE = "07831062"


@dataclass
class TestCase:
    input_text: str
    expected_text: str
    description: Optional[str] = None


@dataclass
class TestGroup:
    group_name: str
    cases: List[TestCase]


# Mehrgliedrige Test-Definition
TEST_SUITE: List[TestGroup] = [
    TestGroup(
        group_name="1. Personen & Orte (Basis)",
        cases=[
            TestCase(
                input_text="Herr Rossi suchte das Glück in München.",
                expected_text="[PER_1] suchte das Glück in [LOC_1].",
                description="Klassische Einzelentitäten",
            ),
            TestCase(
                input_text="Robert Meggle wohnt in Augsburg.",
                expected_text="[PER_1] wohnt in [LOC_1].",
                description="Vorname + Nachname und Stadt",
            ),
            TestCase(
                input_text="Sabine reist von Berlin über Hamburg nach Köln.",
                expected_text="[PER_1] reist von [LOC_1] über [LOC_2] nach [LOC_3].",
                description="Mehrere Orte in einem Satz",
            ),
            TestCase(
                input_text="Sabine arbeitet in Berlin. Sabines Arbeitplatz ist aber in Hamburg.",
                expected_text="[PER_1] arbeitet in [LOC_1]. [PER_1] Arbeitplatz ist aber in [LOC_2].",
                description="Genitiv und Wiederholung der gleichen Identität",
            ),
            TestCase(
                input_text="Robert hat ein Auto. Roberts Auto ist rot.",
                expected_text="[PER_1] hat ein Auto. [PER_1] Auto ist rot.",
                description="Genitiv des Subjektes der gleichen Identität",
            ),
        ],
    ),
    TestGroup(
        group_name="2. Namensidentitäten & Anrede-Splits",
        cases=[
            TestCase(
                input_text="Herr Meggle fährt Auto. Frau Meggle auch.",
                expected_text="[PER_1] fährt Auto. [PER_2] auch.",
                description="Gleicher Nachname mit unterschiedlichen Anreden",
            ),
            TestCase(
                input_text="Markus Hofmann hat entschieden. Markus Hofmann geht nach Hause.",
                expected_text="[PER_1] hat entschieden. [PER_1] geht nach Hause.",
                description="Wiederholte Nennung derselben Identität",
            ),
        ],
    ),
    TestGroup(
        group_name="3. Juristischer Kontext & Behörden",
        cases=[
            TestCase(
                input_text="Das Landgericht München I hat unter dem Aktenzeichen 31 O 12345/23 entschieden.",
                expected_text="[ORG_1] hat unter dem Aktenzeichen [CASE_NR_1] entschieden.",
                description="Gerichtsbezeichnung und Aktenzeichen",
            ),
            TestCase(
                input_text="Der Beklagte Schneider bestreitet die Aussagen der Zeugin Sabine Fischer.",
                expected_text="Der Beklagte [PER_1] bestreitet die Aussagen der Zeugin [PER_2].",
                description="Rollen im Prozess (Beklagter/Zeugin)",
            ),
        ],
    ),
    TestGroup(
        group_name="4. False-Positive-Prävention (Zahlen, Versionen, Paragraphen)",
        cases=[
            TestCase(
                input_text="In Paragraph 12.05. steht Version 1.2. ist live.",
                expected_text="In Paragraph 12.05. steht Version 1.2. ist live.",
                description="Softwareversionen und Paragraphennummern",
            ),
            TestCase(
                input_text="Die Verfassungswidrigkeit des §219a StGB war Thema.",
                expected_text="Die Verfassungswidrigkeit des §219a StGB war Thema.",
                description="Gesetzesparagraphen",
            ),
        ],
    ),
    TestGroup(
        group_name="5. Organisationen & Rechtsformen",
        cases=[
            TestCase(
                input_text="Die Siemens AG und die Testfirma GmbH & Co. KG starten ein Projekt.",
                expected_text="Die [ORG_1] und die [ORG_2] starten ein Projekt.",
                description="Kombinierte deutsche Unternehmensformen",
            ),
            TestCase(
                input_text="Vertreten durch die Rechtsanwälte Dr. Weber & Partner mbB in Augsburg.",
                expected_text="Vertreten durch die Rechtsanwälte [ORG_1] in [LOC_1].",
                description="Kanzleinamen mit Partnerschaftsform",
            ),
        ],
    ),
    TestGroup(
        group_name="6. Eigene Enitäten",
        cases=[
            TestCase(
                input_text="Die Fallnummer ist 0815",
                expected_text="Die Fallnummer ist [CASE_NR_1]",
                description="Fallnummern als eigene Entität",
              
            )
        ],
    ),    
]


class LetheAPIClient:

    def __init__(self, base_url: str, access_code: str):
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "X-Access-Code": access_code,
        }
        # SSL-Verifikation für lokale Self-Signed-Zertifikate deaktivieren
        self.ssl_ctx = ssl.create_default_context()
        self.ssl_ctx.check_hostname = False
        self.ssl_ctx.verify_mode = ssl.CERT_NONE

    def _post(self, endpoint: str, payload: dict) -> dict:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=data, headers=self.headers, method="POST"
        )
        with urllib.request.urlopen(req, context=self.ssl_ctx) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def anonymize(self, text: str) -> dict:
        return self._post("anonymize", {"text": text})

    def deanonymize(self, text: str, session_id: str) -> dict:
        return self._post(
            "deanonymize", {"text": text, "session_id": session_id}
        )


def colorize_tags(text: str) -> str:
    # Färbt Platzhalter wie [PER_1], [LOC_1] in Cyan
    return re.sub(r"(\[[A-Z_0-9]+\])", r"\033[96m\1\033[0m", text)


def run_tests():
    client = LetheAPIClient(BASE_URL, ACCESS_CODE)
    total_tests = sum(len(g.cases) for g in TEST_SUITE)
    passed_anonymize = 0
    passed_roundtrip = 0
    failed_tests = 0

    print(f"\033[1;34m==================================================")
    print(f"Starte Lethe Core Testsuite ({total_tests} Tests in {len(TEST_SUITE)} Gruppen)")
    print(f"Ziel: {BASE_URL}")
    print(f"==================================================\033[0m\n")

    test_counter = 1
    for group in TEST_SUITE:
        print(f"\033[1;33m>>> Gruppe: {group.group_name}\033[0m")

        for case in group.cases:
            prefix = f"  [{test_counter:02d}/{total_tests:02d}]"
            desc = f" ({case.description})" if case.description else ""
            print(f"{prefix} Test{desc}:")
            print(f"    Eingabe:   {case.input_text}")
            print(f"    Erwartet:  {colorize_tags(case.expected_text)}")

            try:
# 1. Anonymize Call
                res_anon = client.anonymize(case.input_text)
                actual_anon = res_anon.get("anonymized_text", "")
                session_id = res_anon.get("session_id")

                print(f"    Erhalten:  {colorize_tags(actual_anon)}")

                anon_success = (actual_anon.strip() == case.expected_text.strip())
                roundtrip_success = False
                actual_restored = ""
                raw_deanon_response = {}

                # 2. Deanonymize Call
                if session_id:
                    raw_deanon_response = client.deanonymize(actual_anon, session_id)
                    # Prüfe gängige Key-Namen flexibel ab:
                    actual_restored = (
                        raw_deanon_response.get("restored_text")
                        or raw_deanon_response.get("deanonymized_text")
                        or raw_deanon_response.get("text")
                        or ""
                    )
                    roundtrip_success = (actual_restored.strip() == case.input_text.strip())

                if anon_success and roundtrip_success:
                    print(f"    Status:    \033[92m[SUCCESS]\033[0m (Anon & Roundtrip OK)")
                    passed_anonymize += 1
                    passed_roundtrip += 1
                else:
                    print(f"    Status:    \033[91m[FAIL]\033[0m")
                    if not anon_success:
                        print(f"      \033[93m[Diff Anon]\033[0m")
                        print(f"        Soll: {repr(case.expected_text)}")
                        print(f"        Ist:  {repr(actual_anon)}")
                    if not roundtrip_success:
                        print(f"      \033[93m[Diff Roundtrip]\033[0m")
                        print(f"        Soll (Original): {repr(case.input_text)}")
                        print(f"        Ist  (Restored): {repr(actual_restored)}")
                        print(f"        Raw Response:    {raw_deanon_response}")
                    failed_tests += 1

            except urllib.error.HTTPError as e:
                print(
                    f"    Status:    \033[91m[HTTP ERROR {e.code}]\033[0m: {e.read().decode('utf-8')}"
                )
                failed_tests += 1
            except Exception as e:
                print(f"    Status:    \033[91m[ERROR]\033[0m: {e}")
                failed_tests += 1

            print()
            test_counter += 1

    # Abschlussbericht
    all_ok = failed_tests == 0
    status_color = "\033[1;92m" if all_ok else "\033[1;91m"
    print(f"{status_color}==================================================")
    print(f"ZUSAMMENFASSUNG:")
    print(
        f"  Anonymisierung korrekt: {passed_anonymize}/{total_tests}"
    )
    print(f"  Roundtrip korrekt:      {passed_roundtrip}/{total_tests}")
    print(f"  Fehlgeschlagen:         {failed_tests}/{total_tests}")
    print(f"==================================================\033[0m")

    if not all_ok:
        sys.exit(1)


if __name__ == "__main__":
    run_tests()