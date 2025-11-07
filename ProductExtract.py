# ProductExtract.py

import json
import os

# Definiert die Pfade relativ zum Stammverzeichnis, in dem das Skript liegt.
INPUT_JSON_PATH = os.path.join('content', '06_products.json')
OUTPUT_MD_PATH = 'products_summary.md'

# === FELD-SETS ===

# Felder für KURZZUSAMMENFASSUNG (Option 1)
FIELDS_SHORT = [
    'product_code',
    'product_name',
    'modality_name',
    'product_type',
    'therapeutic_area',
    'current_phase',
    'project_status',
    'expected_launch_year'
]

# Felder für UMFASSENDE TECH-DEV TABELLE (Option 2)
FIELDS_COMPREHENSIVE = [
    # Core Identity
    'product_code',
    'product_name',
    'modality_name',
    'product_type',
    'therapeutic_area',
    
    # Development Status
    'current_phase',
    'project_status',
    'expected_launch_year',
    'lead_indication',
    
    # Scientific Context
    'mechanism_of_action',
    'short_description',
    'patient_population',
    
    # Manufacturing & CMC
    'dosage_form',
    'route_of_administration',
    'base_technology',
    'primary_packaging',
    'ppq_status',
    'critical_path_item',
    'ppq_details',
    'biel_category',
    
    # Timeline
    'timeline_variance_days',
    'timeline_variance_baseline',
    
    # Supply Chain
    'ds_volume_category',
    'dp_volume_category',
    'ds_suppliers',
    'dp_suppliers',
    'device_partners',
    
    # Risks
    'operational_risks',
    'timeline_risks',
    'supply_chain_risks',
    
    # Regulatory
    'regulatory_details',
    'submission_status',
    'launch_geography',
    
    # Process Link
    'process_template_name'
]

# === FORMATIERUNGSFUNKTIONEN ===

def format_suppliers(suppliers_list):
    """
    Formatiert eine Liste von Suppliers (JSONB) für Markdown-Tabelle.
    Beispiel: [{"name": "PPG", "status": "halted"}, {"name": "Thermo"}]
    Output: "PPG (halted); Thermo"
    """
    if not suppliers_list or not isinstance(suppliers_list, list):
        return ''
    
    formatted = []
    for supplier in suppliers_list:
        if isinstance(supplier, dict):
            name = supplier.get('name', 'Unknown')
            status = supplier.get('status')
            site = supplier.get('site')
            
            parts = [name]
            if site:
                parts.append(f"@{site}")
            if status:
                parts.append(f"({status})")
            
            formatted.append(' '.join(parts))
    
    return '; '.join(formatted)

def format_device_partners(partners_list):
    """
    Formatiert Device Partners (JSONB) für Markdown-Tabelle.
    Beispiel: [{"name": "Nemera", "device_type": "PEN", "role": "Primary"}]
    Output: "Nemera (PEN/Primary)"
    """
    if not partners_list or not isinstance(partners_list, list):
        return ''
    
    formatted = []
    for partner in partners_list:
        if isinstance(partner, dict):
            name = partner.get('name', 'Unknown')
            device_type = partner.get('device_type', '')
            role = partner.get('role', '')
            
            info = '/'.join(filter(None, [device_type, role]))
            if info:
                formatted.append(f"{name} ({info})")
            else:
                formatted.append(name)
    
    return '; '.join(formatted)

def format_risks(risks_dict):
    """
    Formatiert Risks (JSONB) für Markdown-Tabelle.
    Beispiel: {"high": ["Risk1", "Risk2"], "medium": [], "critical": ["Risk3"]}
    Output: "CRIT: 1 | HIGH: 2 | MED: 0"
    """
    if not risks_dict or not isinstance(risks_dict, dict):
        return ''
    
    critical = len(risks_dict.get('critical', []))
    high = len(risks_dict.get('high', []))
    medium = len(risks_dict.get('medium', []))
    
    if critical + high + medium == 0:
        return 'None'
    
    parts = []
    if critical > 0:
        parts.append(f"CRIT: {critical}")
    if high > 0:
        parts.append(f"HIGH: {high}")
    if medium > 0:
        parts.append(f"MED: {medium}")
    
    return ' | '.join(parts)

def format_ppq_details(ppq_dict):
    """
    Formatiert PPQ Details (JSONB) für Markdown-Tabelle.
    Beispiel: {"DS": {"PPG": "halted"}, "DP": null}
    Output: "DS: PPG=halted | DP: -"
    """
    if not ppq_dict or not isinstance(ppq_dict, dict):
        return ''
    
    parts = []
    for key in ['DS', 'DP']:
        value = ppq_dict.get(key)
        if value and isinstance(value, dict):
            status = ', '.join([f"{k}={v}" for k, v in value.items()])
            parts.append(f"{key}: {status}")
        elif value:
            parts.append(f"{key}: {value}")
        else:
            parts.append(f"{key}: -")
    
    return ' | '.join(parts)

def format_regulatory_details(reg_dict):
    """
    Formatiert Regulatory Details (JSONB) für Markdown-Tabelle.
    Beispiel: {"Obesity": ["FDA Breakthrough", "FDA Fast Track"]}
    Output: "Obesity: 2 designations"
    """
    if not reg_dict or not isinstance(reg_dict, dict):
        return ''
    
    parts = []
    for indication, designations in reg_dict.items():
        if isinstance(designations, list):
            count = len(designations)
            if count > 0:
                parts.append(f"{indication}: {count} designation{'s' if count > 1 else ''}")
    
    return '; '.join(parts) if parts else 'None'

def format_field_value(field_name, value):
    """
    Formatiert einen Feldwert basierend auf seinem Typ.
    Speziell für JSONB-Felder.
    """
    if value is None:
        return ''
    
    # JSONB-Felder mit spezieller Formatierung
    if field_name in ['ds_suppliers', 'dp_suppliers']:
        return format_suppliers(value)
    elif field_name == 'device_partners':
        return format_device_partners(value)
    elif field_name in ['operational_risks', 'timeline_risks', 'supply_chain_risks']:
        return format_risks(value)
    elif field_name == 'ppq_details':
        return format_ppq_details(value)
    elif field_name == 'regulatory_details':
        return format_regulatory_details(value)
    
    # Standard-Formatierung
    return str(value)

def clean_for_md_table(value):
    """
    Bereinigt einen Wert, damit er sicher in eine Markdown-Tabellenzelle eingefügt werden kann.
    - Behandelt None-Werte.
    - Konvertiert in einen String.
    - Entfernt Zeilenumbrüche und Pipe-Zeichen, die die Tabellenstruktur zerstören würden.
    """
    if value is None or value == '':
        return ''
    # Ersetzt Pipes und Zeilenumbrüche, um das Tabellenformat nicht zu zerstören
    return str(value).replace('|', '¦').replace('\n', ' ').replace('\r', '')

def get_user_choice():
    """
    Fragt den User nach dem gewünschten Tabellen-Umfang.
    """
    print("\n" + "="*60)
    print("PRODUKT-EXPORT: Wähle den Tabellen-Umfang")
    print("="*60)
    print("1 - Kurzzusammenfassung (8 Felder)")
    print("2 - Umfassende Tech-Dev Tabelle (34 Felder)")
    print("="*60)
    
    while True:
        choice = input("\nDeine Wahl (1 oder 2): ").strip()
        if choice in ['1', '2']:
            return choice
        print("❌ Ungültige Eingabe. Bitte '1' oder '2' eingeben.")

def create_product_summary(fields_to_use, output_suffix=''):
    """
    Extrahiert Produktinformationen aus einer großen JSON-Datei und schreibt sie
    in eine kompakte Markdown-Tabelle.
    
    Args:
        fields_to_use: Liste der zu extrahierenden Felder
        output_suffix: Suffix für den Ausgabe-Dateinamen
    """
    # Output-Pfad anpassen wenn Suffix vorhanden
    output_path = OUTPUT_MD_PATH
    if output_suffix:
        base, ext = os.path.splitext(OUTPUT_MD_PATH)
        output_path = f"{base}_{output_suffix}{ext}"
    
    print(f"\n🔄 Starte die Produktextraktion aus '{INPUT_JSON_PATH}'...")

    # --- 1. JSON-Daten lesen ---
    try:
        with open(INPUT_JSON_PATH, 'r', encoding='utf-8') as f:
            products = json.load(f)
    except FileNotFoundError:
        print(f"❌ FEHLER: Eingabedatei unter '{INPUT_JSON_PATH}' nicht gefunden.")
        print("Bitte stelle sicher, dass die Datei 'content/06_products.json' existiert.")
        return
    except json.JSONDecodeError:
        print(f"❌ FEHLER: JSON aus '{INPUT_JSON_PATH}' konnte nicht verarbeitet werden. Bitte überprüfe das Dateiformat.")
        return

    if not isinstance(products, list):
        print("❌ FEHLER: Die JSON-Datei sollte eine Liste von Produkten enthalten (ein Array von Objekten).")
        return

    print(f"✅ {len(products)} Produkte in der JSON-Datei gefunden.")

    # --- 2. Markdown-Tabelle schreiben ---
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Product Summary\n\n")
            
            # Tabellenkopf schreiben
            header_titles = [field.replace('_', ' ').title() for field in fields_to_use]
            f.write(f"| {' | '.join(header_titles)} |\n")

            # Trennlinie schreiben
            separators = ['---'] * len(fields_to_use)
            f.write(f"| {' | '.join(separators)} |\n")

            # Tabellenzeilen schreiben
            for product in sorted(products, key=lambda p: p.get('product_code', '')):
                row_values = []
                for field in fields_to_use:
                    raw_value = product.get(field)
                    formatted_value = format_field_value(field, raw_value)
                    cleaned_value = clean_for_md_table(formatted_value)
                    row_values.append(cleaned_value)
                
                f.write(f"| {' | '.join(row_values)} |\n")

    except IOError as e:
        print(f"❌ FEHLER: Konnte nicht in die Ausgabedatei '{output_path}' schreiben.\n{e}")
        return

    print(f"\n✅ Erfolg! Die Produktübersicht wurde unter '{output_path}' erstellt.")

if __name__ == "__main__":
    # User-Auswahl
    choice = get_user_choice()
    
    if choice == '1':
        print("\n📋 Erstelle Kurzzusammenfassung...")
        create_product_summary(FIELDS_SHORT, 'short')
    else:
        print("\n📊 Erstelle umfassende Tech-Dev Tabelle...")
        create_product_summary(FIELDS_COMPREHENSIVE, 'comprehensive')
    
    print("\n" + "="*60)
    print("✨ Export abgeschlossen!")
    print("="*60 + "\n")