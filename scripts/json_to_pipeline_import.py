import json
from datetime import datetime
from collections import defaultdict

# ============================================
# KONFIGURATION
# ============================================
INPUT_DRUG_SUBSTANCE = 'drug_substance_export.json'
INPUT_DRUG_PRODUCT = 'drug_product_export.json'

OUTPUT_DRUG_SUBSTANCES = 'drug_substances.json'
OUTPUT_DRUG_PRODUCTS = 'drug_products.json'
OUTPUT_PROJECTS = 'projects.json'

# ============================================
# HILFSFUNKTIONEN
# ============================================

def parse_date(date_str):
    """
    Konvertiert verschiedene Datumsformate in YYYY-MM-DD
    """
    if not date_str or date_str == '(Blank)':
        return None
    
    date_str = str(date_str).strip()
    
    # Format: "2026-Jan-07" → "2026-01-07"
    try:
        dt = datetime.strptime(date_str, "%Y-%b-%d")
        return dt.strftime("%Y-%m-%d")
    except:
        pass
    
    # Format: YYYY/MM oder YYYY-MM
    if len(date_str) == 7 and ('/' in date_str or '-' in date_str):
        year, month = date_str.replace('/', '-').split('-')
        return f"{year}-{month.zfill(2)}-01"
    
    # Format: YYYY
    if len(date_str) == 4 and date_str.isdigit():
        return f"{date_str}-01-01"
    
    # Format: YYYY-MM-DD (bereits korrekt)
    if len(date_str) == 10:
        return date_str
    
    # Mehrere Daten (z.B. "2020/02 2026/01") → nimm das erste
    if ' ' in date_str:
        return parse_date(date_str.split()[0])
    
    return None

def clean_value(value):
    """Bereinigt Werte: (Blank) → None, Strings trimmen"""
    if not value or value == '(Blank)':
        return None
    return str(value).strip()

def extract_fields_dict(fields):
    """Konvertiert fields-Array in Dict: {field_name: value}"""
    return {f['field_name']: clean_value(f['value']) for f in fields}

def extract_table_rows(table_data):
    """
    Konvertiert Tabellen-Daten in strukturierte Rows
    Input: Array von {row, col, field_name, value}
    Output: Array von Dicts (ein Dict pro Row)
    """
    rows_dict = defaultdict(dict)
    
    for entry in table_data:
        row_idx = entry['row']
        field_name = entry['field_name']
        value = clean_value(entry['value'])
        
        rows_dict[row_idx][field_name] = value
    
    # Sortiert nach row_idx zurückgeben
    return [rows_dict[i] for i in sorted(rows_dict.keys())]

# ============================================
# 1. DRUG SUBSTANCES PARSEN
# ============================================

def parse_drug_substances(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    drug_substances = []
    all_projects = []
    
    for file_obj in data['files']:
        for page in file_obj['pages']:
            # Top-Level-Felder extrahieren
            fields = extract_fields_dict(page['fields'])
            
            ds = {
                "code": fields.get('Code'),
                "inn": fields.get('INN'),
                "molecule_type": fields.get('Molecule Type'),
                "mechanism_of_action": fields.get('Mechanism of Action'),
                "technology": fields.get('Technology'),
                "storage_conditions": fields.get('Storage Conditions'),
                "shelf_life": fields.get('Shelf Life'),
                "development_approach": fields.get('Development Approach'),
                "development_site": fields.get('Development Site'),
                "launch_site": fields.get('Launch Site'),
                "release_site": fields.get('Release Site'),
                "routine_site": fields.get('Routine Site'),
                "demand_category": fields.get('Demand Category'),
                "demand_launch_year": fields.get('Demand Launch Year'),
                "demand_peak_year": fields.get('Demand Peak Year'),
                "peak_demand_range": fields.get('Peak Demand Range'),
                "commercial": fields.get('Commercial'),
                "status": fields.get('Status'),
                "type": fields.get('Type'),
                "biel": fields.get('Biel'),
                "d_and_dl_ops": fields.get('D&DL-OPS:'),
                "last_refresh": parse_date(fields.get('Last Refresh')),
                "modality_name": fields.get('Molecule Type')  # Fallback
            }
            
            drug_substances.append(ds)
            
            # Projects aus Tabelle extrahieren
            if 'tables' in page:
                for table_name, table_data in page['tables'].items():
                    rows = extract_table_rows(table_data)
                    
                    for row in rows:
                        project = {
                            "name": row.get('ProjectName'),
                            "indication": row.get('Indication'),
                            "project_type": row.get('Project Type'),
                            "administration": row.get('Administration'),
                            "sod": parse_date(row.get('SoD')),
                            "dsmm3": parse_date(row.get('DSMM3')),
                            "dsmm4": parse_date(row.get('DSMM4')),
                            "dpmm3": parse_date(row.get('DPMM3')),
                            "dpmm4": parse_date(row.get('DPMM4')),
                            "rofd": parse_date(row.get('RoFD')),
                            "submission": parse_date(row.get('Submission')),
                            "launch": parse_date(row.get('Launch')),
                            "drug_substance_codes": [ds['code']],
                            "drug_product_codes": []
                        }
                        
                        if project['name']:  # Nur wenn ProjectName vorhanden
                            all_projects.append(project)
    
    return drug_substances, all_projects

# ============================================
# 2. DRUG PRODUCTS PARSEN
# ============================================

def parse_drug_products(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    drug_products = []
    all_projects = []
    
    for file_obj in data['files']:
        for page in file_obj['pages']:
            fields = extract_fields_dict(page['fields'])
            
            dp = {
                "code": fields.get('Code'),
                "pharm_form": fields.get('Pharm Form'),
                "technology": fields.get('Technology'),
                "classification": fields.get('Classification'),
                "storage_conditions": fields.get('Storage Conditions'),
                "transport_conditions": fields.get('Transport Conditions'),
                "holding_time": fields.get('Hodling Time'),  # Typo im Original
                "development_approach": fields.get('Development Approach'),
                "development_site": fields.get('Development Site'),
                "launch_site": fields.get('Launch Site'),
                "release_site": fields.get('Release Site'),
                "routine_site": fields.get('Routine Site'),
                "demand_category": fields.get('Demand Category'),
                "demand_launch_year": fields.get('Demand Lanch Year'),  # Typo im Original
                "demand_peak_year": fields.get('Demand Peak Year'),
                "peak_demand_range": fields.get('Peak Demand Range'),
                "commercial": fields.get('Commercial'),
                "strategic_technology": fields.get('Strategic Technology'),
                "d_and_dl_ops": fields.get('D&DL-OPS:'),
                "last_refresh": parse_date(fields.get('Last Refresh')),
                "drug_substance_codes": []  # Wird später gefüllt
            }
            
            drug_products.append(dp)
            
            # Projects aus Tabelle extrahieren
            if 'tables' in page:
                for table_name, table_data in page['tables'].items():
                    rows = extract_table_rows(table_data)
                    
                    for row in rows:
                        project = {
                            "name": row.get('projectname'),  # Kleinschreibung bei DP!
                            "indication": row.get('Indication'),
                            "project_type": row.get('projectType'),  # camelCase bei DP!
                            "administration": row.get('Administration'),
                            "sod": parse_date(row.get('SoD')),
                            "dsmm3": parse_date(row.get('DSMM3')),
                            "dsmm4": parse_date(row.get('DSMM4')),
                            "dpmm3": parse_date(row.get('DPMM3')),
                            "dpmm4": parse_date(row.get('DPMM4')),
                            "rofd": parse_date(row.get('RoFD')),
                            "submission": parse_date(row.get('Submission')),
                            "launch": parse_date(row.get('Launch')),
                            "drug_substance_codes": [],
                            "drug_product_codes": [dp['code']]
                        }
                        
                        if project['name']:
                            all_projects.append(project)
    
    return drug_products, all_projects

# ============================================
# 3. PROJECTS KONSOLIDIEREN
# ============================================

def consolidate_projects(projects_from_ds, projects_from_dp):
    """
    Merged Projects aus beiden Quellen anhand des Namens
    """
    projects_dict = {}
    
    # Alle Projects durchgehen
    for project in projects_from_ds + projects_from_dp:
        name = project['name']
        
        if name not in projects_dict:
            # Neues Project
            projects_dict[name] = project
        else:
            # Merge: DS/DP-Codes zusammenführen
            existing = projects_dict[name]
            
            # DS-Codes mergen
            for ds_code in project['drug_substance_codes']:
                if ds_code and ds_code not in existing['drug_substance_codes']:
                    existing['drug_substance_codes'].append(ds_code)
            
            # DP-Codes mergen
            for dp_code in project['drug_product_codes']:
                if dp_code and dp_code not in existing['drug_product_codes']:
                    existing['drug_product_codes'].append(dp_code)
            
            # Timeline-Daten: Nimm das neueste/vollständigste
            for field in ['sod', 'dsmm3', 'dsmm4', 'dpmm3', 'dpmm4', 'rofd', 'submission', 'launch']:
                if not existing[field] and project[field]:
                    existing[field] = project[field]
            
            # Andere Felder: Nimm das erste nicht-None
            for field in ['indication', 'project_type', 'administration']:
                if not existing[field] and project[field]:
                    existing[field] = project[field]
    
    return list(projects_dict.values())

# ============================================
# 4. DRUG PRODUCTS mit DS-Codes verknüpfen
# ============================================

def link_drug_products_to_substances(drug_products, projects):
    """
    Fügt drug_substance_codes zu Drug Products hinzu
    basierend auf gemeinsamen Projects
    """
    dp_to_ds = defaultdict(set)
    
    for project in projects:
        for dp_code in project['drug_product_codes']:
            for ds_code in project['drug_substance_codes']:
                if dp_code and ds_code:
                    dp_to_ds[dp_code].add(ds_code)
    
    # Drug Products aktualisieren
    for dp in drug_products:
        dp['drug_substance_codes'] = list(dp_to_ds.get(dp['code'], []))
    
    return drug_products

# ============================================
# MAIN
# ============================================

if __name__ == '__main__':
    print("🚀 Starte JSON → JSON Konvertierung...")
    
    # 1. Drug Substances parsen
    print("\n📦 Parse Drug Substances...")
    drug_substances, projects_from_ds = parse_drug_substances(INPUT_DRUG_SUBSTANCE)
    print(f"   ✓ {len(drug_substances)} Drug Substances gefunden")
    print(f"   ✓ {len(projects_from_ds)} Projects aus DS extrahiert")
    
    # 2. Drug Products parsen
    print("\n📦 Parse Drug Products...")
    drug_products, projects_from_dp = parse_drug_products(INPUT_DRUG_PRODUCT)
    print(f"   ✓ {len(drug_products)} Drug Products gefunden")
    print(f"   ✓ {len(projects_from_dp)} Projects aus DP extrahiert")
    
    # 3. Projects konsolidieren
    print("\n🔗 Konsolidiere Projects...")
    projects = consolidate_projects(projects_from_ds, projects_from_dp)
    print(f"   ✓ {len(projects)} eindeutige Projects")
    
    # 4. Drug Products mit DS verknüpfen
    print("\n🔗 Verknüpfe Drug Products mit Drug Substances...")
    drug_products = link_drug_products_to_substances(drug_products, projects)
    
    # 5. Statistiken
    print("\n📊 Statistiken:")
    print(f"   • Drug Substances: {len(drug_substances)}")
    print(f"   • Drug Products: {len(drug_products)}")
    print(f"   • Projects: {len(projects)}")
    print(f"   • Projects mit DS: {sum(1 for p in projects if p['drug_substance_codes'])}")
    print(f"   • Projects mit DP: {sum(1 for p in projects if p['drug_product_codes'])}")
    print(f"   • Projects mit Timeline: {sum(1 for p in projects if p['launch'])}")
    
    # 6. JSON-Dateien schreiben
    print("\n💾 Schreibe JSON-Dateien...")
    
    with open(OUTPUT_DRUG_SUBSTANCES, 'w', encoding='utf-8') as f:
        json.dump(drug_substances, f, indent=2, ensure_ascii=False)
    print(f"   ✓ {OUTPUT_DRUG_SUBSTANCES}")
    
    with open(OUTPUT_DRUG_PRODUCTS, 'w', encoding='utf-8') as f:
        json.dump(drug_products, f, indent=2, ensure_ascii=False)
    print(f"   ✓ {OUTPUT_DRUG_PRODUCTS}")
    
    with open(OUTPUT_PROJECTS, 'w', encoding='utf-8') as f:
        json.dump(projects, f, indent=2, ensure_ascii=False)
    print(f"   ✓ {OUTPUT_PROJECTS}")
    
    print("\n✅ Fertig! Import-Reihenfolge:")
    print("   1. drug_substances.json")
    print("   2. drug_products.json")
    print("   3. projects.json")
    
    # 7. Beispiel-Output (erste 2 Einträge)
    print("\n📄 Beispiel Drug Substance:")
    print(json.dumps(drug_substances[0], indent=2, ensure_ascii=False))
    
    if drug_products:
        print("\n📄 Beispiel Drug Product:")
        print(json.dumps(drug_products[0], indent=2, ensure_ascii=False))
    
    if projects:
        print("\n📄 Beispiel Project:")
        print(json.dumps(projects[0], indent=2, ensure_ascii=False))