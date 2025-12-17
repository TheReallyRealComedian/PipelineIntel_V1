#!/usr/bin/env python3
"""
Transformiert results.json in das Import-Format für PipelineIntelligence.

Erstellt drei Dateien:
1. modalities_import.json - Für Data Management > Modalities Import (ZUERST!)
2. challenges_import.json - Für Data Management > Challenges Import
3. challenge_modality_details_import.json - Für Challenge Modality Details Import

Usage:
    python transform_challenges.py
"""

import json
from pathlib import Path

# Mapping von JSON-Modalitätsnamen zu DB-Modalitätsnamen mit Kategorien
MODALITY_CONFIG = {
    "ADC": {
        "name": "ADC",
        "category": "Biologics",
        "short_description": "Antibody-Drug Conjugates",
        "description": "Targeted biopharmaceuticals combining monoclonal antibodies with cytotoxic drugs via chemical linkers."
    },
    "GeneTherapy": {
        "name": "Gene Therapy",
        "category": "Advanced Therapy",
        "short_description": "Viral Vector Gene Therapy",
        "description": "Therapeutic approaches using viral vectors (AAV, Lentivirus) to deliver genetic material for treating genetic disorders."
    },
    "LiveBacteria": {
        "name": "Live Bacteria",
        "category": "Biologics",
        "short_description": "Live Biotherapeutic Products (LBPs)",
        "description": "Therapeutic products containing live microorganisms for treating diseases through microbiome modulation."
    },
    "Oligonucleotide": {
        "name": "Oligonucleotide",
        "category": "Chemical",
        "short_description": "Oligonucleotide Therapeutics",
        "description": "Synthetic nucleic acid-based therapeutics including ASOs, siRNAs, and mRNAs."
    },
    "OV": {
        "name": "Oncolytic Virus",
        "category": "Advanced Therapy",
        "short_description": "Oncolytic Virotherapy",
        "description": "Engineered or naturally occurring viruses that selectively replicate in and destroy cancer cells."
    },
    "Peptides": {
        "name": "Peptide",
        "category": "Chemical",
        "short_description": "Peptide Therapeutics",
        "description": "Short chains of amino acids used as therapeutic agents, typically 2-50 amino acids."
    },
    "PROTAC": {
        "name": "PROTAC",
        "category": "Chemical",
        "short_description": "Proteolysis Targeting Chimeras",
        "description": "Bifunctional molecules that induce targeted protein degradation via the ubiquitin-proteasome system."
    },
    "RecombinantProtein": {
        "name": "Recombinant Protein",
        "category": "Biologics",
        "short_description": "Recombinant Protein Therapeutics",
        "description": "Proteins produced through recombinant DNA technology, including enzymes, hormones, and cytokines."
    }
}

# Simple name mapping for backwards compatibility
MODALITY_NAME_MAP = {key: val["name"] for key, val in MODALITY_CONFIG.items()}


def transform_challenges(input_file: str, output_dir: str = None):
    """Transformiert die results.json in Import-kompatible Formate."""

    input_path = Path(input_file)
    output_dir = Path(output_dir) if output_dir else input_path.parent

    with open(input_path, 'r', encoding='utf-8-sig') as f:
        data = json.load(f)

    challenges = []
    modality_details = []

    for item in data:
        # Skip items without challenge_name (e.g. summary objects)
        if 'challenge_name' not in item:
            continue

        # 1. Transform main challenge data
        challenge = {
            "name": item.get("challenge_name"),
            "value_step": item.get("value_step"),
            "agnostic_description": item.get("description_summary"),
            "agnostic_root_cause": transform_root_causes(
                item.get("modalitätsagnostische_wurzelursachen", [])
            )
        }
        challenges.append(challenge)

        # 2. Transform modality-specific details
        bewertung = item.get("modalitätsspezifische_bewertung", {})
        wurzelursachen = item.get("modalitätsspezifische_wurzelursachen", {})

        for modality_key, scores in bewertung.items():
            db_modality_name = MODALITY_NAME_MAP.get(modality_key, modality_key)

            # Get modality-specific root causes
            specific_causes = wurzelursachen.get(modality_key, [])

            detail = {
                "challenge_name": item.get("challenge_name"),  # For reference
                "modality_name": db_modality_name,
                "specific_description": scores.get("severity_rationale"),
                "specific_root_cause": transform_root_causes(specific_causes),
                "impact_score": scores.get("severity_score_1_to_5"),
                "impact_details": scores.get("severity_rationale"),
                "maturity_score": scores.get("BRL", {}).get("overall_brl"),
                "maturity_details": format_brl_details(scores.get("BRL", {})),
                "trends_3_5_years": None  # Wird aus cross_modalität_vergleich geholt falls vorhanden
            }
            modality_details.append(detail)

        # Check for trend data in cross_modalität_vergleich
        if "cross_modalität_vergleich" in item:
            trend = item["cross_modalität_vergleich"].get("trend_3_to_5_years")
            if trend:
                # Add trend to all modality details of this challenge
                for detail in modality_details:
                    if detail["challenge_name"] == item.get("challenge_name"):
                        detail["trends_3_5_years"] = trend

    # 1. Create modalities import file
    modalities = []
    for key, config in MODALITY_CONFIG.items():
        modalities.append({
            "modality_name": config["name"],
            "modality_category": config["category"],
            "short_description": config["short_description"],
            "description": config["description"]
        })

    modalities_file = output_dir / "modalities_import.json"
    with open(modalities_file, 'w', encoding='utf-8') as f:
        json.dump(modalities, f, indent=2, ensure_ascii=False)
    print(f"✓ Wrote {len(modalities)} modalities to {modalities_file}")

    # 2. Write challenges file
    challenges_file = output_dir / "challenges_import.json"
    with open(challenges_file, 'w', encoding='utf-8') as f:
        json.dump(challenges, f, indent=2, ensure_ascii=False)
    print(f"✓ Wrote {len(challenges)} challenges to {challenges_file}")

    # 3. Write modality details file
    details_file = output_dir / "challenge_modality_details_import.json"
    with open(details_file, 'w', encoding='utf-8') as f:
        json.dump(modality_details, f, indent=2, ensure_ascii=False)
    print(f"✓ Wrote {len(modality_details)} modality details to {details_file}")

    # Print summary
    print(f"\n{'='*60}")
    print("TRANSFORMATION COMPLETE")
    print(f"{'='*60}")
    print(f"Modalities: {len(modalities)}")
    print(f"Challenges: {len(challenges)}")
    print(f"Modality Details: {len(modality_details)}")
    print(f"\nImport-Reihenfolge:")
    print(f"1. ZUERST: modalities_import.json via Data Management > Modalities")
    print(f"2. DANN: challenges_import.json via Data Management > Challenges")
    print(f"3. ZULETZT: challenge_modality_details_import.json via Data Management > Challenge Modality Details")

    return modalities, challenges, modality_details


def transform_root_causes(causes_list: list) -> str:
    """Konvertiert eine Liste von Root Causes in einen formatierten Text."""
    if not causes_list:
        return None

    # Join with bullet points
    formatted = "\n".join(f"• {cause}" for cause in causes_list)
    return formatted


def format_brl_details(brl: dict) -> str:
    """Formatiert BRL-Details in einen lesbaren Text."""
    if not brl:
        return None

    parts = []

    if "technical" in brl:
        parts.append(f"Technical BRL: {brl['technical']}/10")
        if brl.get("technical_rationale"):
            parts.append(f"  {brl['technical_rationale']}")

    if "quality" in brl:
        parts.append(f"Quality BRL: {brl['quality']}/10")
        if brl.get("quality_rationale"):
            parts.append(f"  {brl['quality_rationale']}")

    if "operational" in brl:
        parts.append(f"Operational BRL: {brl['operational']}/10")
        if brl.get("operational_rationale"):
            parts.append(f"  {brl['operational_rationale']}")

    if "overall_brl" in brl:
        parts.append(f"\nOverall BRL: {brl['overall_brl']}/10")

    return "\n".join(parts) if parts else None


if __name__ == "__main__":
    script_dir = Path(__file__).parent
    input_file = script_dir / "results.json"

    if not input_file.exists():
        print(f"Error: {input_file} not found")
        exit(1)

    transform_challenges(str(input_file))
