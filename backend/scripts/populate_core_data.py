import sys
import os

# Add the project root to the Python path to allow for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.app import create_app
from backend.db import db
from backend.models import Modality, ManufacturingCapability

def populate_initial_modalities(session):
    """Populate basic modality classifications"""
    print("Populating initial modalities...")
    modalities_to_add = [
        {"modality_name": "Small Molecule", "modality_category": "Chemical"},
        {"modality_name": "Monoclonal Antibody", "modality_category": "Biologics"},
        {"modality_name": "CAR-T", "modality_category": "Advanced Therapy"},
        {"modality_name": "Gene Therapy", "modality_category": "Advanced Therapy"},
        {"modality_name": "ADC", "modality_category": "Biologics"},
        {"modality_name": "mRNA Vaccine", "modality_category": "Advanced Therapy"},
    ]
    
    for mod_data in modalities_to_add:
        exists = session.query(Modality).filter_by(modality_name=mod_data["modality_name"]).first()
        if not exists:
            modality = Modality(**mod_data)
            session.add(modality)
            print(f"  - Added modality: {mod_data['modality_name']}")
        else:
            print(f"  - Modality '{mod_data['modality_name']}' already exists. Skipping.")
    session.commit()
    print("Modalities population complete.")


def populate_basic_capabilities(session):
    """Populate fundamental manufacturing capabilities"""
    print("\nPopulating basic capabilities...")
    capabilities_to_add = [
        {"capability_name": "API Synthesis", "capability_category": "Chemical Production", "complexity_weight": 5},
        {"capability_name": "Cell Culture", "capability_category": "Biologics Production", "complexity_weight": 7},
        {"capability_name": "BSL-2+ Containment", "capability_category": "Safety & Containment", "complexity_weight": 8},
        {"capability_name": "Chromatography", "capability_category": "Purification", "complexity_weight": 6},
        {"capability_name": "Aseptic Fill & Finish", "capability_category": "Drug Product", "complexity_weight": 7},
        {"capability_name": "Viral Vector Production", "capability_category": "Advanced Therapy Production", "complexity_weight": 10},
        {"capability_name": "Cellular Therapy Processing", "capability_category": "Advanced Therapy Production", "complexity_weight": 10},
    ]

    for cap_data in capabilities_to_add:
        exists = session.query(ManufacturingCapability).filter_by(capability_name=cap_data["capability_name"]).first()
        if not exists:
            capability = ManufacturingCapability(**cap_data)
            session.add(capability)
            print(f"  - Added capability: {cap_data['capability_name']}")
        else:
            print(f"  - Capability '{cap_data['capability_name']}' already exists. Skipping.")
    session.commit()
    print("Capabilities population complete.")


if __name__ == "__main__":
    # Create a Flask app instance to establish an application context
    app = create_app()
    with app.app_context():
        # The db object is now properly configured
        populate_initial_modalities(db.session)
        populate_basic_capabilities(db.session)
        print("\nInitial data population script finished successfully.")