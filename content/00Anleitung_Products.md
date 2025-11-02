# Detaillierte Anleitung: 06_products.json erstellen und validieren

## Inhaltsverzeichnis
1. [Übersicht](#übersicht)
2. [Vorbereitung: Referenztabellen](#vorbereitung-referenztabellen)
3. [Product JSON Struktur](#product-json-struktur)
4. [Schritt-für-Schritt Anleitung](#schritt-für-schritt-anleitung)
5. [Fremdschlüssel-Validierung](#fremdschlüssel-validierung)
6. [Challenge-Verknüpfungen](#challenge-verknüpfungen)
7. [Technology-Verknüpfungen](#technology-verknüpfungen)
8. [Validierungs-Checklisten](#validierungs-checklisten)
9. [Häufige Fehler](#häufige-fehler)

---

## Übersicht

Das **06_products.json** File ist das komplexeste der 6 Injection-Files, da es Referenzen auf **alle vorherigen Files** enthält:
- ✅ Modalities (01)
- ✅ Process Stages (02) - indirekt über Technologies
- ✅ Process Templates (03)
- ✅ Technologies (04)
- ✅ Challenges (05)

**Kritische Regel:** Jede Referenz muss **exakt** mit den Namen in den Referenztabellen in diesem Dokument übereinstimmen (Groß-/Kleinschreibung beachten!).

---

## Vorbereitung: Referenztabellen

Diese Tabellen enthalten alle gültigen Namen, die Sie für die Verknüpfung in Ihrer `06_products.json`-Datei benötigen. **Verwenden Sie immer Copy-Paste aus diesen Tabellen**, um Tippfehler zu vermeiden.

### 1. Modalitäten-Referenztabelle

| Modalitäts-Name (exakt!) | Kategorie | Template verfügbar? |
| :--- | :--- | :--- |
| ADC | Engineered Biologics | ✅ |
| Bacteria | Advanced Therapy | ✅ |
| Base/Prime Editing | Emerging Therapy | ✅ |
| CAR-NK | Emerging Therapy | ✅ |
| CAR-T | Advanced Therapy | ✅ |
| Gene Therapy | Advanced Therapy | ✅ |
| Molecular Glues | Emerging Biologics | ✅ |
| Monoclonal Antibody | Biologics | ✅ |
| Oligonucleotides | Nucleic Acids | ✅ |
| Onkolytische Viren | Advanced Therapy | ✅ |
| PROTAC | Engineered Biologics | ✅ |
| Peptides | Biologics | ✅ |
| Prescription Digital Therapeutic (SaMD/PDT) | Digital Therapeutics | ✅ |
| Radiopharmaceuticals | Emerging Therapy | ✅ |
| Recombinant Proteins | Biologics | ✅ |
| Small Molecule | Traditional | ✅ |
| Stem Cell Therapies | Advanced Therapy | ✅ |
| T-cell Engager | Engineered Biologics | ✅ |
| TCR-T | Emerging Therapy | ✅ |
| Trispecific Antibodies | Emerging Biologics | ✅ |

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

### 3. Technologies-Referenztabelle

| Technology Name (exakt!) | Stage | Gilt für Modalitäten | Generic? |
| :--- | :--- | :--- | :--- |
| Allogeneic Cell Bank Manufacturing | Cell Line Development | Stem Cell Therapies, CAR-T | Nein |
| Amorphous Solid Dispersion (ASD) Technology | Physical Form Development | Molecular Glues, PROTAC, Small Molecule | Nein |
| Antibody-Drug Conjugation (ADC) | Conjugation & Modification | ADC | Nein |
| Aseptic Container Filling | Primary Container Filling | ADC, Base/Prime Editing, Gene Therapy, Monoclonal Antibody, Oligonucleotides, Peptides, Radiopharmaceuticals, Recombinant Proteins, Stem Cell Therapies, T-cell Engager, Trispecific Antibodies | Nein |
| Auto-Injector Integration | Container Closure & Device Integration | [ALLE] | Ja |
| Automated Radiosynthesis | Conjugation & Modification | Radiopharmaceuticals | Nein |
| Automated Visual Inspection (AVI) | Visual Inspection & Quality Verification | [ALLE] | Ja |
| Baculovirus-Sf9 System (AAV) | Chemical/Biological Production | Gene Therapy | Nein |
| Bacterial Fermentation Platform | Chemical/Biological Production | Bacteria, Recombinant Proteins | Nein |
| Bioconjugation Chemistry | Conjugation & Modification | ADC, Oligonucleotides, Peptides, PROTAC | Nein |
| Blow-Fill-Seal (BFS) | Primary Container Filling | [ALLE] | Ja |
| CHO Cell Culture Platform | Chemical/Biological Production | Monoclonal Antibody, Recombinant Proteins, T-cell Engager | Nein |
| CRISPR/Cas9 Cell Line Engineering | Cell Line Development | CAR-T, Gene Therapy, Stem Cell Therapies | Nein |
| Capillary Electrophoresis (CE) | Advanced Analytical Methods | [ALLE] | Ja |
| Cell Line Stability & Banking | Cell Line Development | ADC, Bacteria, Base/Prime Editing, CAR-NK, CAR-T, Gene Therapy, Monoclonal Antibody, Oligonucleotides, Peptides, Radiopharmaceuticals, Recombinant Proteins, Small Molecule, Stem Cell Therapies, T-cell Engager, TCR-T, Trispecific Antibodies | Nein |
| Cold Chain Monitoring | Cold Chain & Distribution | ADC, Bacteria, Base/Prime Editing, CAR-NK, CAR-T, Gene Therapy, Monoclonal Antibody, Oligonucleotides, Peptides, Radiopharmaceuticals, Recombinant Proteins, Stem Cell Therapies, T-cell Engager, TCR-T, Trispecific Antibodies | Nein |
| Continuous Chromatography | Chromatography & Advanced Purification | Monoclonal Antibody, Recombinant Proteins | Nein |
| Continuous Flow Chemistry | Process Intensification | Small Molecule | Nein |
| Controlled-Rate Cryopreservation | Container Closure & Device Integration | CAR-T, CAR-NK, Stem Cell Therapies, TCR-T | Nein |
| Cryogenic Reaction Technology | Process Intensification | Small Molecule | Nein |
| Crystallization & Polymorphism Control | Physical Processing & Drying | Small Molecule | Nein |
| Depth Filtration | Primary Recovery & Clarification | [ALLE] | Ja |
| Design of Experiments (DoE) | Quality by Design (QbD) Implementation | [ALLE] | Ja |
| Direct Compression | Solid Dosage Manufacturing | Small Molecule | Nein |
| Fluid Bed Coating | Solid Dosage Manufacturing | Small Molecule | Nein |
| Focused Beam Reflectance Measurement (FBRM) | Process Analytical Technology (PAT) | Small Molecule | Nein |
| GalNAc Conjugation Technology | Physical Form Development | Oligonucleotides | Nein |
| HEK293 Cell Culture System | Chemical/Biological Production | Gene Therapy, Onkolytische Viren | Nein |
| High-Performance Liquid Chromatography (HPLC) | Chromatography & Advanced Purification | [ALLE] | Ja |
| Hot-Melt Extrusion (HME) | Solid Dosage Manufacturing | Small Molecule | Nein |
| Hydrophobic Interaction Chromatography (HIC) | Chromatography & Advanced Purification | [ALLE] | Ja |
| Ion Exchange Chromatography (IEX) | Chromatography & Advanced Purification | [ALLE] | Ja |
| Isolator Technology (Aseptic) | Aseptic Processing | [ALLE] | Ja |
| Large-Scale Hydrogenation | Chemical/Biological Production | Small Molecule | Nein |
| Lentiviral Vector Production | Chemical/Biological Production | CAR-T, CAR-NK, TCR-T, Gene Therapy, Stem Cell Therapies | Nein |
| Lipid Nanoparticle (LNP) Formulation | Physical Form Development | Oligonucleotides, Gene Therapy | Nein |
| Low pH Viral Inactivation | Viral Safety & Impurity Clearance | Monoclonal Antibody, Recombinant Proteins | Nein |
| Lyophilization (Freeze-Drying) | Lyophilization & Stabilization | ADC, Bacteria, Gene Therapy, Monoclonal Antibody, Oligonucleotides, Peptides, Recombinant Proteins, Stem Cell Therapies | Nein |
| Mammalian Cell Line Engineering | Cell Line Development | ADC, Monoclonal Antibody, Recombinant Proteins, T-cell Engager, Trispecific Antibodies | Nein |
| Microbial Fermentation (E. coli) | Chemical/Biological Production | Recombinant Proteins, Peptides | Nein |
| Microfluidic Mixing | Physical Form Development | Oligonucleotides, Gene Therapy | Nein |
| Mixed-Mode Chromatography | Chromatography & Advanced Purification | [ALLE] | Ja |
| Multi-Attribute Method (MAM) | Advanced Analytical Methods | Monoclonal Antibody, Recombinant Proteins, T-cell Engager, ADC | Nein |
| Multi-Step Organic Synthesis | Chemical/Biological Production | Small Molecule | Nein |
| NK Cell Expansion | Upstream Processing | CAR-NK | Nein |
| Nanofiltration (20nm) | Viral Safety & Impurity Clearance | [ALLE] | Ja |
| Near-Infrared Spectroscopy (NIR) | Process Analytical Technology (PAT) | [ALLE] | Ja |
| PEGylation | Conjugation & Modification | Recombinant Proteins, Peptides | Nein |
| PROTAC Synthesis Platform | Chemical/Biological Production | PROTAC | Nein |
| Perfusion Cell Culture | Process Intensification | Monoclonal Antibody, Recombinant Proteins | Nein |
| Phosphoramidite Chemistry (Oligonucleotide Synthesis) | Chemical/Biological Production | Oligonucleotides, Base/Prime Editing | Nein |
| Plaque-Forming Unit (PFU) Assay | Advanced Analytical Methods | Onkolytische Viren, Gene Therapy | Nein |
| Pre-Filled Syringe Technology | Primary Container Filling | [ALLE] | Ja |
| Process Simulation & Digital Twin | Quality by Design (QbD) Implementation | [ALLE] | Ja |
| Protein A Affinity Chromatography | Chromatography & Advanced Purification | Monoclonal Antibody, T-cell Engager, Trispecific Antibodies, ADC | Nein |
| Quantitative PCR (qPCR) for Genome-Titer | Advanced Analytical Methods | Onkolytische Viren, Gene Therapy | Nein |
| Radiolabeling Chemistry | Conjugation & Modification | Radiopharmaceuticals | Nein |
| Raman Spectroscopy (PAT) | Process Analytical Technology (PAT) | [ALLE] | Ja |
| Single-Use Systems (Biologics) | Aseptic Processing | [ALLE] | Ja |
| Site-Specific Conjugation | Conjugation & Modification | ADC | Nein |
| Size Exclusion Chromatography (SEC) | Chromatography & Advanced Purification | [ALLE] | Ja |
| Solid-Phase Peptide Synthesis (SPPS) | Chemical/Biological Production | Peptides | Nein |
| Solvent/Detergent Treatment | Viral Safety & Impurity Clearance | [ALLE] | Ja |
| Spray Drying | Physical Processing & Drying | Small Molecule, Peptides, Oligonucleotides | Nein |
| T-Cell Expansion (Ex Vivo) | Upstream Processing | CAR-T, TCR-T | Nein |
| Tangential Flow Filtration (TFF) | Primary Recovery & Clarification | [ALLE] | Ja |
| Track & Trace Serialization | Secondary Packaging & Serialization | [ALLE] | Ja |
| Triple Plasmid Transfection (AAV) | Chemical/Biological Production | Gene Therapy | Nein |
| Twin Screw Granulation (TSG) | Solid Dosage Manufacturing | Small Molecule | Nein |
| Ultracentrifugation (Viral Vectors) | Primary Recovery & Clarification | Gene Therapy, Onkolytische Viren | Nein |
| Vero/BHK Cell Culture System (HSV-1) | Chemical/Biological Production | Onkolytische Viren | Nein |
| Viral Transduction (T-Cell/NK-Cell) | Chemical/Biological Production | CAR-T, CAR-NK, TCR-T | Nein |

### 4. Challenges-Referenztabelle

| Challenge Name (exakt!) | Technology | Severity | Gilt für Modalitäten |
| :--- | :--- | :--- | :--- |
| ADC Dual-Stream Manufacturing | Antibody-Drug Conjugation (ADC) | critical | ADC |
| Advanced Formulation | Amorphous Solid Dispersion (ASD) Technology | major | Molecular Glues, PROTAC, Small Molecule |
| Advanced Peptide Manufacturing | Solid-Phase Peptide Synthesis (SPPS) | major | Peptides |
| Advanced Purification | Continuous Chromatography | major | Monoclonal Antibody, Recombinant Proteins |
| Allogeneic HLA Immunogenicity & Rejection | Allogeneic Cell Bank Manufacturing | critical | Stem Cell Therapies, CAR-T |
| Amorphous Solid Dispersion (ASD) Manufacturing | Amorphous Solid Dispersion (ASD) Technology | major | Molecular Glues, PROTAC, Small Molecule |
| Autologous Cell Processing | T-Cell Expansion (Ex Vivo) | critical | CAR-T, TCR-T |
| BSL-2+ Containment Facilities Required | Lentiviral Vector Production | critical | CAR-T, CAR-NK, TCR-T, Gene Therapy, Stem Cell Therapies |
| Bispecific Antibody Chain Pairing | Mammalian Cell Line Engineering | major | ADC, Monoclonal Antibody, Recombinant Proteins, T-cell Engager, Trispecific Antibodies |
| CRISPR Off-Target Mutagenesis & Validation | CRISPR/Cas9 Cell Line Engineering | major | CAR-T, Gene Therapy, Stem Cell Therapies |
| Cold Chain Logistics | Cold Chain Monitoring | critical | ADC, Bacteria, Base/Prime Editing, CAR-NK, CAR-T, Gene Therapy, Monoclonal Antibody, Oligonucleotides, Peptides, Radiopharmaceuticals, Recombinant Proteins, Stem Cell Therapies, T-cell Engager, TCR-T, Trispecific Antibodies |
| Complex Biologics Manufacturing | HEK293 Cell Culture System | moderate | Gene Therapy, Onkolytische Viren |
| Complex Purification | High-Performance Liquid Chromatography (HPLC) | major | [ALLE] |
| Covalent Inhibitor Stability Control | Cryogenic Reaction Technology | major | Small Molecule |
| Cryopreservation | Controlled-Rate Cryopreservation | critical | CAR-T, CAR-NK, Stem Cell Therapies, TCR-T |
| Delivery System Integration | Lipid Nanoparticle (LNP) Formulation | critical | Oligonucleotides, Gene Therapy |
| Device & Combination Product Manufacturing | Auto-Injector Integration | critical | [ALLE] |
| Downstream Purification | Protein A Affinity Chromatography | major | Monoclonal Antibody, T-cell Engager, Trispecific Antibodies, ADC |
| Empty Capsid Separation for Gene Therapy | Ultracentrifugation (Viral Vectors) | critical | Gene Therapy, Onkolytische Viren |
| Extractables & Leachables from Single-Use Components | Single-Use Systems (Biologics) | major | [ALLE] |
| Heterobifunctional PROTAC Synthesis Scale-Up | PROTAC Synthesis Platform | critical | PROTAC |
| High Titer Production (>5g/L) | Perfusion Cell Culture | moderate | Monoclonal Antibody, Recombinant Proteins |
| High-Potency API (HPAPI) Handling | Bioconjugation Chemistry | critical | ADC, Oligonucleotides, Peptides, PROTAC |
| High-Selectivity Synthesis Requirements | Multi-Step Organic Synthesis | major | Small Molecule |
| Hydrogen Safety & Explosion Risk Management | Large-Scale Hydrogenation | critical | Small Molecule |
| Neutralizing Antibody Response | Vero/BHK Cell Culture System (HSV-1) | major | Onkolytische Viren |
| Personalized Manufacturing Logistics | T-Cell Expansion (Ex Vivo) | critical | CAR-T, TCR-T |
| Polymorphic Form Control & Stability | Crystallization & Polymorphism Control | critical | Small Molecule |
| Potency Assay for Dual Mechanism of Action | Plaque-Forming Unit (PFU) Assay | major | Onkolytische Viren, Gene Therapy |
| Protein A Chromatography Cost & Ligand Leaching | Protein A Affinity Chromatography | major | Monoclonal Antibody, T-cell Engager, Trispecific Antibodies, ADC |
| Specialized Solid-Phase Synthesis | Phosphoramidite Chemistry (Oligonucleotide Synthesis) | major | Oligonucleotides, Base/Prime Editing |
| Stability Management | Lyophilization (Freeze-Drying) | major | ADC, Bacteria, Gene Therapy, Monoclonal Antibody, Oligonucleotides, Peptides, Recombinant Proteins, Stem Cell Therapies |
| Tumor Microenvironment (TME) Penetration | HEK293 Cell Culture System | major | Gene Therapy, Onkolytische Viren |
| Viral Safety Testing | Lentiviral Vector Production | critical | CAR-T, CAR-NK, TCR-T, Gene Therapy, Stem Cell Therapies |
| Viral Transduction | Viral Transduction (T-Cell/NK-Cell) | critical | CAR-T, CAR-NK, TCR-T |
| Viral Vector Production Complexity | Lentiviral Vector Production | critical | CAR-T, CAR-NK, TCR-T, Gene Therapy, Stem Cell Therapies |

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
  "modality_name": "Small Molecule",       // ✅ Muss in Modalitäten-Referenztabelle existieren
  
  // ========================================
  // WICHTIGE FREMDSCHLÜSSEL
  // ========================================
  "process_template_name": "Standard Small Molecule Process",  // ✅ Muss zu modality_name passen
  "base_technology": "Twin Screw Granulation (TSG)",      // Optional, ✅ muss in Technologies-Referenztabelle existieren
  
  // ========================================
  // BASISDATEN & BESCHREIBUNGEN
  // ========================================
  "product_type": "NCE",
  "therapeutic_area": "Oncology",
  "current_phase": "Phase 2",
  "short_description": "Kurze Beschreibung (1-2 Sätze)",
  "description": "Ausführliche Beschreibung des Produkts...",
  "mechanism_of_action": "Beschreibung des Wirkmechanismus...",

  // ========================================
  // WEITERE OPTIONALE FELDER (gekürzt)
  // ========================================
  "lead_indication": "NSCLC",
  "expected_launch_year": 2028,
  "dosage_form": "Tablet",
  "route_of_administration": "Oral",
  "timeline_variance_days": 0,
  
  // ========================================
  // TECHNOLOGIES (many-to-many)
  // ========================================
  "technology_names": [                    // Optional Array
    "Direct Compression",                  // ✅ Muss in Technologies-Referenztabelle existieren
    "Track & Trace Serialization"
  ],
  
  // ========================================
  // CHALLENGES (many-to-many mit Metadata)
  // ========================================
  "explicit_challenges": [                 // Optional Array
    {
      "challenge_name": "Polymorphic Form Control & Stability",  // ✅ Muss in Challenges-Referenztabelle existieren
      "relationship_type": "explicit"      // Immer "explicit"
    }
  ],
  "excluded_challenges": [                 // Optional Array
    {
      "challenge_name": "Hydrogen Safety & Explosion Risk Management", // ✅ Muss in Challenges-Referenztabelle existieren
      "relationship_type": "excluded"      // Immer "excluded"
    }
  ]
}
```

---

## Schritt-für-Schritt Anleitung

### Schritt 1: Basis-Information sammeln

Für jedes Produkt brauchst du:
- `product_code` (eindeutig), `product_name`, `modality_name`, `therapeutic_area`, `current_phase`, etc.

### Schritt 2: Modalität auswählen

1.  Finde die exakte Modalität in der **Modalitäten-Referenztabelle**.
2.  Kopiere den Namen **exakt** in das Feld `modality_name`.

```json
{
  "product_code": "BI 1015550",
  "product_name": "Nerandomilast",
  "modality_name": "Small Molecule"  // ✅ Exakte Kopie aus Referenztabelle
}
```

### Schritt 3: Process Template zuweisen

1.  Filtere die **Process Templates-Referenztabelle** nach der `modality_name` aus Schritt 2.
2.  Wähle das passende Template und kopiere den Namen **exakt**.

**Beispiel:**
Für Modalität: "Small Molecule", ist das verfügbare Template: "Standard Small Molecule Process".

```json
{
  "modality_name": "Small Molecule",
  "process_template_name": "Standard Small Molecule Process"  // ✅ Passt zur Modalität
}
```
**Fehler:** Ein `process_template_name` von "Standard Monoclonal Antibody Process" wäre hier ungültig.

### Schritt 4: Base Technology angeben (optional)

1.  Suche in der **Technologies-Referenztabelle** nach Technologien, die für deine Modalität gelten oder "generic" ([ALLE]) sind.
2.  Wähle die Haupt-Technologie des Produkts und kopiere den Namen **exakt**.

```json
{
  "modality_name": "Small Molecule",
  "base_technology": "Twin Screw Granulation (TSG)"  // ✅ Gilt für "Small Molecule"
}
```

### Schritt 5: Weitere Technologien hinzufügen (optional)

Füge weitere relevante Technologien aus der **Technologies-Referenztabelle** in das `technology_names` Array ein.

```json
{
  "base_technology": "Twin Screw Granulation (TSG)",
  "technology_names": [
    "Direct Compression",
    "Fluid Bed Coating",
    "Track & Trace Serialization"  // ✅ Generic, also gültig
  ]
}
```

### Schritt 6: Challenges verknüpfen (optional)

1.  **`explicit_challenges`**: Füge Challenges hinzu, die das Produkt explizit hat.
2.  **`excluded_challenges`**: Füge Challenges hinzu, die explizit **nicht** für dieses Produkt gelten (überschreibt Vererbung).
3.  Kopiere die Namen **exakt** aus der **Challenges-Referenztabelle**.

```json
{
  "explicit_challenges": [
    {
      "challenge_name": "Polymorphic Form Control & Stability",
      "relationship_type": "explicit"
    }
  ],
  "excluded_challenges": [
    {
      "challenge_name": "Amorphous Solid Dispersion (ASD) Manufacturing",
      "relationship_type": "excluded"
    }
  ]
}
```

### Schritt 7: Restliche Felder ausfüllen

Fülle die verbleibenden Felder wie `therapeutic_area`, `current_phase`, Beschreibungen etc. aus.

---

## Fremdschlüssel-Validierung

Für **jedes** Produkt-Objekt gilt:

1.  **Modalität**: `modality_name` muss in der Modalitäten-Tabelle existieren.
2.  **Process Template**: `process_template_name` muss in der Template-Tabelle existieren UND zur `modality_name` passen.
3.  **Base Technology**: `base_technology` (falls gesetzt) muss in der Technologie-Tabelle existieren UND zur Modalität passen oder generic sein.
4.  **Technology Names**: Jeder Name im Array muss in der Technologie-Tabelle existieren UND zur Modalität passen oder generic sein.
5.  **Challenges**: Jeder `challenge_name` in `explicit_challenges` und `excluded_challenges` muss in der Challenge-Tabelle existieren.

---

## Challenge-Verknüpfungen

Ein Produkt erbt Challenges aus drei Quellen:

1.  **Modalität**: Standard-Challenges der Modalität.
2.  **Process Template**: Challenges, die mit den Technologien im Template verknüpft sind.
3.  **Produkt selbst**:
    *   `explicit_challenges`: Fügt Challenges hinzu.
    *   `excluded_challenges`: Entfernt Challenges (überschreibt Vererbung von 1 & 2).

---

## Technology-Verknüpfungen

Ein Produkt erbt Technologien aus drei Quellen:

1.  **Template-spezifisch**: Technologien, die im `process_template_name` definiert sind.
2.  **Modalitäts-spezifisch**: Technologien, die für die `modality_name` des Produkts gelten.
3.  **Generic**: Technologien, die für alle Modalitäten gelten.

---

## Validierungs-Checklisten

### Pre-Import Checklist

-   [ ] File ist valides JSON (z.B. mit [jsonlint.com](https://jsonlint.com) prüfen).
-   [ ] File ist ein Array von Objekten: `[{...}, {...}]`.
-   [ ] Keine doppelten `product_code` Werte.

### Per-Product Checklist

-   [ ] `product_code` ist eindeutig.
-   [ ] `modality_name` existiert in der Referenztabelle (exakte Schreibweise!).
-   [ ] `process_template_name` (falls gesetzt) existiert und passt zur Modalität (exakte Schreibweise!).
-   [ ] `base_technology` (falls gesetzt) existiert und passt zur Modalität (exakte Schreibweise!).
-   [ ] Jeder Eintrag in `technology_names` existiert und passt zur Modalität (exakte Schreibweise!).
-   [ ] Jeder `challenge_name` existiert in der Referenztabelle (exakte Schreibweise!).
-   [ ] Keine Challenge erscheint sowohl in `explicit_challenges` als auch `excluded_challenges`.

---

## Häufige Fehler

-   **Fehler 1: Tippfehler in Namen**
    -   **Problem**: `"modality_name": "Monoclonale Antibody"` (Falsch)
    -   **Lösung**: Immer Copy-Paste aus den Referenztabellen. Korrekt: `"modality_name": "Monoclonal Antibody"`.

-   **Fehler 2: Template passt nicht zur Modalität**
    -   **Problem**: `modality_name: "Small Molecule"`, `process_template_name: "Standard Monoclonal Antibody Process"` (Falsch)
    -   **Lösung**: Prüfe in der Template-Tabelle. Korrekt: `process_template_name: "Standard Small Molecule Process"`.

-   **Fehler 3: Technology gilt nicht für Modalität**
    -   **Problem**: `modality_name: "Small Molecule"`, `base_technology: "CHO Cell Culture Platform"` (Falsch)
    -   **Lösung**: Prüfe in der Technologie-Tabelle. Korrekt: `base_technology: "Direct Compression"`.

-   **Fehler 4: Challenge-Name existiert nicht**
    -   **Problem**: `"challenge_name": "High Titer Production"` (Unvollständig)
    -   **Lösung**: Copy-Paste den exakten Namen. Korrekt: `"challenge_name": "High Titer Production (>5g/L)"`.

-   **Fehler 5: Challenge in beiden Arrays**
    -   **Problem**: Dieselbe Challenge ist in `explicit_challenges` und `excluded_challenges`.
    -   **Lösung**: Eine Challenge kann nur entweder hinzugefügt oder ausgeschlossen werden.

-   **Fehler 6: Falscher `relationship_type`**
    -   **Problem**: `relationship_type: "included"` (Falsch)
    -   **Lösung**: Nur `"explicit"` oder `"excluded"` sind erlaubt.