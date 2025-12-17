# Detaillierte Anleitung: 06_products.json erstellen und validieren

## Inhaltsverzeichnis
1. [Übersicht](#übersicht)
2. [Vorbereitung: Referenztabellen](#vorbereitung-referenztabellen)
3. [Product JSON Struktur](#product-json-struktur)
4. [Schritt-für-Schritt Anleitung](#schritt-für-schritt-anleitung)
5. [Fremdschlüssel-Validierung](#fremdschlüssel-validierung)
6. [Challenge-Verknüpfungen](#challenge-verknüpfungen)
7. [Validierungs-Checklisten](#validierungs-checklisten)
8. [Häufige Fehler](#häufige-fehler)

---

## Übersicht

Das **06_products.json** File enthält alle Produktdaten mit Referenzen auf:

- Modalities (01)
- Process Templates (03)

**Kritische Regel:** Jede Referenz muss **exakt** mit den Namen in den Referenztabellen übereinstimmen (Groß-/Kleinschreibung beachten!).

### Vereinfachtes Schema (Version 3.0)

Das Datenbankschema wurde radikal vereinfacht:

- **Challenges** werden jetzt über die **Modalität** des Produkts vererbt
- Jede Challenge hat **modality-spezifische Details** (Impact Score, Maturity Score, etc.)
- Keine direkten Product-Challenge oder Product-Technology Verknüpfungen mehr

---

## Vorbereitung: Referenztabellen

Diese Tabellen enthalten alle gültigen Namen für die Verknüpfung. **Verwenden Sie immer Copy-Paste**, um Tippfehler zu vermeiden.

### 1. Modalitäten-Referenztabelle

| Modalitäts-Name (exakt!) | Kategorie | Template verfügbar? |
| :--- | :--- | :--- |
| ADC | Engineered Biologics | Ja |
| Bacteria | Advanced Therapy | Ja |
| Base/Prime Editing | Emerging Therapy | Ja |
| CAR-NK | Emerging Therapy | Ja |
| CAR-T | Advanced Therapy | Ja |
| Gene Therapy | Advanced Therapy | Ja |
| Molecular Glues | Emerging Biologics | Ja |
| Monoclonal Antibody | Biologics | Ja |
| Oligonucleotides | Nucleic Acids | Ja |
| Onkolytische Viren | Advanced Therapy | Ja |
| PROTAC | Engineered Biologics | Ja |
| Peptides | Biologics | Ja |
| Prescription Digital Therapeutic (SaMD/PDT) | Digital Therapeutics | Ja |
| Radiopharmaceuticals | Emerging Therapy | Ja |
| Recombinant Proteins | Biologics | Ja |
| Small Molecule | Traditional | Ja |
| Stem Cell Therapies | Advanced Therapy | Ja |
| T-cell Engager | Engineered Biologics | Ja |
| TCR-T | Emerging Therapy | Ja |
| Trispecific Antibodies | Emerging Biologics | Ja |

### 2. Process Templates-Referenztabelle

| Template Name (exakt!) | Gehört zu Modalität | Anzahl Stages |
| :--- | :--- | :--- |
| Standard ADC Process | ADC | 11 |
| Standard Bacteria Process | Bacteria | 9 |
| Standard Base/Prime Editing Process | Base/Prime Editing | 8 |
| Standard CAR-NK Process | CAR-NK | 10 |
| Standard CAR-T Process | CAR-T | 9 |
| Standard Gene Therapy Process | Gene Therapy | 9 |
| Standard Molecular Glues Process | Molecular Glues | 8 |
| Standard Monoclonal Antibody Process | Monoclonal Antibody | 10 |
| Standard Oligonucleotides Process | Oligonucleotides | 8 |
| Standard Oncolytic Virus Process | Onkolytische Viren | 4 |
| Standard PROTAC Process | PROTAC | 8 |
| Standard Peptides Process | Peptides | 8 |
| Standard Prescription Digital Therapeutic (SaMD/PDT) Process | Prescription Digital Therapeutic (SaMD/PDT) | 8 |
| Standard Radiopharmaceuticals Process | Radiopharmaceuticals | 8 |
| Standard Recombinant Proteins Process | Recombinant Proteins | 9 |
| Standard Small Molecule Process | Small Molecule | 8 |
| Standard Stem Cell Therapies Process | Stem Cell Therapies | 9 |
| Standard T-cell Engager Process | T-cell Engager | 8 |
| Standard TCR-T Process | TCR-T | 8 |
| Standard Trispecific Antibodies Process | Trispecific Antibodies | 8 |

---

## Product JSON Struktur

### Vollständiges Schema mit allen Feldern

```json
{
  // ========================================
  // PFLICHTFELDER
  // ========================================
  "product_code": "BI 1234567",           // UNIQUE, Format: "BI XXXXXXX"
  "product_name": "Produktname",           // z.B. "Nerandomilast"
  "modality_name": "Small Molecule",       // Muss in Modalitäten-Referenztabelle existieren

  // ========================================
  // WICHTIGE FREMDSCHLÜSSEL
  // ========================================
  "process_template_name": "Standard Small Molecule Process",  // Muss zu modality_name passen

  // ========================================
  // BASISDATEN & BESCHREIBUNGEN
  // ========================================
  "product_type": "NCE",                   // NCE, NBE, etc.
  "therapeutic_area": "Oncology",
  "current_phase": "Phase 2",
  "short_description": "Kurze Beschreibung (1-2 Sätze)",
  "description": "Ausführliche Beschreibung des Produkts...",
  "mechanism_of_action": "Beschreibung des Wirkmechanismus...",
  "base_technology": "Twin Screw Granulation",  // Freitext-Feld für Haupttechnologie

  // ========================================
  // TIMELINE & STATUS
  // ========================================
  "lead_indication": "NSCLC",
  "expected_launch_year": 2028,
  "project_status": "Active",              // Active, On Hold, Discontinued

  // ========================================
  // FORMULATION & ADMINISTRATION
  // ========================================
  "dosage_form": "Tablet",
  "route_of_administration": "Oral",
  "primary_packaging": "Blister",

  // ========================================
  // NME / LINE-EXTENSION (optional)
  // ========================================
  "is_nme": true,                          // Ist dies ein New Molecular Entity?
  "is_line_extension": false,              // Ist dies eine Line-Extension?
  "parent_product_id": null,               // Falls Line-Extension: ID des NME
  "launch_sequence": 1,                    // Reihenfolge der Launches
  "line_extension_indication": null        // Falls Line-Extension: Indikation
}
```

### Hinweis zu `base_technology`

Das Feld `base_technology` ist ein **Freitext-Feld** zur Beschreibung der Haupttechnologie des Produkts (z.B. "Mammalian", "Twin Screw", "Spray Dried Dispersion"). Es ist keine Referenz auf eine Datenbank-Tabelle.

---

## Schritt-für-Schritt Anleitung

### Schritt 1: Basis-Information sammeln

Für jedes Produkt brauchst du:

- `product_code` (eindeutig)
- `product_name`
- `modality_name`
- `therapeutic_area`
- `current_phase`

### Schritt 2: Modalität auswählen

1. Finde die exakte Modalität in der **Modalitäten-Referenztabelle**.
2. Kopiere den Namen **exakt** in das Feld `modality_name`.

```json
{
  "product_code": "BI 1015550",
  "product_name": "Nerandomilast",
  "modality_name": "Small Molecule"
}
```

### Schritt 3: Process Template zuweisen

1. Filtere die **Process Templates-Referenztabelle** nach der `modality_name` aus Schritt 2.
2. Wähle das passende Template und kopiere den Namen **exakt**.

**Beispiel:**
Für Modalität "Small Molecule" ist das verfügbare Template "Standard Small Molecule Process".

```json
{
  "modality_name": "Small Molecule",
  "process_template_name": "Standard Small Molecule Process"
}
```

**Fehler:** Ein `process_template_name` von "Standard Monoclonal Antibody Process" wäre für "Small Molecule" ungültig.

### Schritt 4: Restliche Felder ausfüllen

Fülle die verbleibenden Felder wie `therapeutic_area`, `current_phase`, `base_technology`, Beschreibungen etc. aus.

```json
{
  "product_code": "BI 1015550",
  "product_name": "Nerandomilast",
  "modality_name": "Small Molecule",
  "process_template_name": "Standard Small Molecule Process",
  "product_type": "NCE",
  "therapeutic_area": "Pulmonology",
  "current_phase": "Phase 3",
  "base_technology": "Twin Screw Granulation",
  "dosage_form": "Tablet",
  "route_of_administration": "Oral",
  "expected_launch_year": 2026
}
```

---

## Fremdschlüssel-Validierung

Für **jedes** Produkt-Objekt gilt:

1. **Modalität**: `modality_name` muss in der Modalitäten-Tabelle existieren.
2. **Process Template**: `process_template_name` muss in der Template-Tabelle existieren UND zur `modality_name` passen.

---

## Challenge-Verknüpfungen

### Vereinfachtes Modell (Version 3.0)

Mit dem neuen Schema werden Challenges **automatisch über die Modalität vererbt**:

```text
Product → Modality → ChallengeModalityDetails → Challenge
```

**Wie es funktioniert:**

1. Ein Produkt hat eine `modality_name` (z.B. "Monoclonal Antibody")
2. Die Modalität ist mit Challenges über `challenge_modality_details` verknüpft
3. Jede Verknüpfung enthält modality-spezifische Informationen:
   - `impact_score` (1-5)
   - `maturity_score` (1-5)
   - `specific_description`
   - `specific_root_cause`
   - `trends_3_5_years`

**Vorteile:**

- Keine manuelle Challenge-Zuordnung pro Produkt nötig
- Challenges werden automatisch aus der Modalität abgeleitet
- Konsistente Challenge-Informationen über alle Produkte einer Modalität

### Challenge-Daten verwalten

Challenges werden separat in zwei Tabellen verwaltet:

1. **`challenges`** - Basis-Informationen (modality-agnostisch):
   - `name`
   - `agnostic_description`
   - `agnostic_root_cause`
   - `value_step` (Upstream, Downstream, etc.)

2. **`challenge_modality_details`** - Modality-spezifische Scores:
   - `challenge_id`
   - `modality_id`
   - `impact_score`
   - `maturity_score`
   - `specific_description`
   - `trends_3_5_years`

---

## Validierungs-Checklisten

### Pre-Import Checklist

- [ ] File ist valides JSON (z.B. mit [jsonlint.com](https://jsonlint.com) prüfen)
- [ ] File ist ein Array von Objekten: `[{...}, {...}]`
- [ ] Keine doppelten `product_code` Werte

### Per-Product Checklist

- [ ] `product_code` ist eindeutig
- [ ] `modality_name` existiert in der Referenztabelle (exakte Schreibweise!)
- [ ] `process_template_name` (falls gesetzt) existiert und passt zur Modalität

---

## Häufige Fehler

### Fehler 1: Tippfehler in Namen

- **Problem**: `"modality_name": "Monoclonale Antibody"` (Falsch)
- **Lösung**: Immer Copy-Paste aus den Referenztabellen. Korrekt: `"modality_name": "Monoclonal Antibody"`

### Fehler 2: Template passt nicht zur Modalität

- **Problem**: `modality_name: "Small Molecule"`, `process_template_name: "Standard Monoclonal Antibody Process"` (Falsch)
- **Lösung**: Prüfe in der Template-Tabelle. Korrekt: `process_template_name: "Standard Small Molecule Process"`

### Fehler 3: Ungültiges JSON-Format

- **Problem**: Trailing Comma, fehlende Anführungszeichen
- **Lösung**: JSON-Validator verwenden vor dem Import

### Fehler 4: Doppelte product_code

- **Problem**: Zwei Produkte mit demselben `product_code`
- **Lösung**: Jeder `product_code` muss eindeutig sein

---

## Änderungshistorie

| Version | Datum | Änderungen |
|---------|-------|------------|
| 3.0 | Dez 2025 | Radikal vereinfacht - Technologies entfernt, Challenges nur über Modality |
| 2.x | Okt 2025 | Technology- und Challenge-Verknüpfungen pro Produkt |
