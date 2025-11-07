# ProductExtract.py

import json
import os

# Definiert die Pfade relativ zum Stammverzeichnis, in dem das Skript liegt.
INPUT_JSON_PATH = os.path.join('content', '06_products.json')
OUTPUT_MD_PATH = 'products_summary.md'

# Felder, die für einen sinnvollen und einfachen Vergleich extrahiert werden sollen.
# Lange Textfelder werden für eine bessere Lesbarkeit der Tabelle vermieden.
FIELDS_TO_EXTRACT = [
    'product_code',
    'product_name',
    'modality_name',
    'product_type',
    'therapeutic_area',
    'current_phase',
    'project_status',
    'expected_launch_year'
]

def clean_for_md_table(value):
    """
    Bereinigt einen Wert, damit er sicher in eine Markdown-Tabellenzelle eingefügt werden kann.
    - Behandelt None-Werte.
    - Konvertiert in einen String.
    - Entfernt Zeilenumbrüche und Pipe-Zeichen, die die Tabellenstruktur zerstören würden.
    """
    if value is None:
        return ''
    # Ersetzt Pipes und Zeilenumbrüche, um das Tabellenformat nicht zu zerstören
    return str(value).replace('|', ',').replace('\n', ' ').replace('\r', '')

def create_product_summary():
    """
    Extrahiert Produktinformationen aus einer großen JSON-Datei und schreibt sie
    in eine kompakte Markdown-Tabelle.
    """
    print(f"Starte die Produktextraktion aus '{INPUT_JSON_PATH}'...")

    # --- 1. JSON-Daten lesen ---
    try:
        with open(INPUT_JSON_PATH, 'r', encoding='utf-8') as f:
            products = json.load(f)
    except FileNotFoundError:
        print(f"FEHLER: Eingabedatei unter '{INPUT_JSON_PATH}' nicht gefunden.")
        print("Bitte stelle sicher, dass die Datei 'content/06_products.json' existiert.")
        return
    except json.JSONDecodeError:
        print(f"FEHLER: JSON aus '{INPUT_JSON_PATH}' konnte nicht verarbeitet werden. Bitte überprüfe das Dateiformat.")
        return

    if not isinstance(products, list):
        print("FEHLER: Die JSON-Datei sollte eine Liste von Produkten enthalten (ein Array von Objekten).")
        return

    print(f"{len(products)} Produkte in der JSON-Datei gefunden.")

    # --- 2. Markdown-Tabelle schreiben ---
    try:
        with open(OUTPUT_MD_PATH, 'w', encoding='utf-8') as f:
            f.write("# Product Summary\n\n")
            
            # Tabellenkopf schreiben
            header_titles = [field.replace('_', ' ').title() for field in FIELDS_TO_EXTRACT]
            f.write(f"| {' | '.join(header_titles)} |\n")

            # Trennlinie schreiben
            separators = ['---'] * len(FIELDS_TO_EXTRACT)
            f.write(f"| {' | '.join(separators)} |\n")

            # Tabellenzeilen schreiben
            for product in sorted(products, key=lambda p: p.get('product_code', '')):
                row_values = [clean_for_md_table(product.get(field)) for field in FIELDS_TO_EXTRACT]
                f.write(f"| {' | '.join(row_values)} |\n")

    except IOError as e:
        print(f"FEHLER: Konnte nicht in die Ausgabedatei '{OUTPUT_MD_PATH}' schreiben.\n{e}")
        return

    print(f"\nErfolg! Die Produktübersicht wurde unter '{OUTPUT_MD_PATH}' erstellt.")

if __name__ == "__main__":
    # Erstellt ein Dummy-Verzeichnis und eine Datei zur Demonstration, falls diese nicht existieren
    if not os.path.exists(INPUT_JSON_PATH):
        print(f"Warnung: '{INPUT_JSON_PATH}' nicht gefunden. Erstelle eine Dummy-Datei zur Demonstration.")
        os.makedirs(os.path.dirname(INPUT_JSON_PATH), exist_ok=True)
        dummy_data = [
            {
                "product_code": "BI 123456",
                "product_name": "Example Product A",
                "modality_name": "T-cell Engager",
                "product_type": "NBE",
                "therapeutic_area": "Oncology",
                "current_phase": "Preclinical",
                "project_status": "Active",
                "expected_launch_year": 2031
            },
            {
                "product_code": "BI 789012",
                "product_name": "Example Product B",
                "modality_name": "Small Molecule",
                "product_type": "NCE",
                "therapeutic_area": "Respiratory",
                "current_phase": "Phase II",
                "project_status": None,
                "expected_launch_year": 2028
            }
        ]
        with open(INPUT_JSON_PATH, 'w', encoding='utf-8') as dummy_file:
            json.dump(dummy_data, dummy_file, indent=4)
    
    create_product_summary()