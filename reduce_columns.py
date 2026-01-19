#!/usr/bin/env python3
"""
Reduce columns in Pipeline_IntellV0.1.csv from 64 to 40 columns.
Removes metadata, redundant columns, and operational details.
"""

import pandas as pd

# Columns to keep with optional renaming (old_name -> new_name)
COLUMNS_TO_KEEP = {
    # Identifikation (5)
    'Match_Status': 'Match_Status',
    'export_Product (name/code)': 'Product_ID',
    'ps_Product Code': 'Product_Code',
    'ps_Product Name': 'Product_Name',
    'ps_Modality Name': 'Modality',

    # Klassifikation (6)
    'export_Classification': 'Classification',
    'ps_Product Type': 'Product_Type',
    'ps_Therapeutic Area': 'Therapeutic_Area',
    'ps_Current Phase': 'Current_Phase',
    'ps_Project Status': 'Project_Status',
    'ps_Lead Indication': 'Lead_Indication',

    # Timeline (3)
    'ps_Expected Launch Year': 'Expected_Launch_Year',
    'ps_Timeline Variance Days': 'Timeline_Variance_Days',
    'ps_Launch Geography': 'Launch_Geography',

    # Manufacturing & Supply (10)
    'export_Commercial': 'Commercial',
    'export_Development Approach': 'Development_Approach',
    'export_Development Site': 'Development_Site',
    'export_Launch Site': 'Launch_Site',
    'export_Pharma Form': 'Pharma_Form',
    'export_Technology': 'Technology',
    'export_Storage Conditions': 'Storage_Conditions',
    'ps_Ds Volume Category': 'DS_Volume_Category',
    'ps_Dp Volume Category': 'DP_Volume_Category',
    'ps_Route Of Administration': 'Route_Of_Administration',

    # Suppliers & Partners (4)
    'ps_Ds Suppliers': 'DS_Suppliers',
    'ps_Dp Suppliers': 'DP_Suppliers',
    'ps_Device Partners': 'Device_Partners',
    'export_D&DL-OPS:': 'Contact_Person',

    # Strategie (4)
    'export_Strategic Class': 'Strategic_Class',
    'export_Strategic Technology': 'Strategic_Technology',
    'export_Demand Category': 'Demand_Category',
    'export_Peak Demand Range': 'Peak_Demand_Range',

    # Risiken (3)
    'ps_Operational Risks': 'Operational_Risks',
    'ps_Timeline Risks': 'Timeline_Risks',
    'ps_Supply Chain Risks': 'Supply_Chain_Risks',

    # Beschreibungen & Regulatorik (5)
    'ps_Mechanism Of Action': 'Mechanism_Of_Action',
    'ps_Short Description': 'Short_Description',
    'ps_Patient Population': 'Patient_Population',
    'ps_Regulatory Details': 'Regulatory_Details',
    'ps_Submission Status': 'Submission_Status',
}


def main():
    print("=" * 60)
    print("Column Reducer for Pipeline_IntellV0.1.csv")
    print("=" * 60)

    # Load CSV
    print("\n[1/3] Loading CSV...")
    df = pd.read_csv('Pipeline_IntellV0.1.csv', delimiter=';', dtype=str)
    print(f"  - Original: {len(df)} rows, {len(df.columns)} columns")

    # Check which columns exist
    print("\n[2/3] Selecting and renaming columns...")
    missing_cols = []
    existing_cols = []

    for old_col in COLUMNS_TO_KEEP.keys():
        if old_col in df.columns:
            existing_cols.append(old_col)
        else:
            missing_cols.append(old_col)

    if missing_cols:
        print(f"  WARNING: {len(missing_cols)} columns not found:")
        for col in missing_cols:
            print(f"    - {col}")

    # Select and rename columns
    df_reduced = df[existing_cols].copy()
    rename_map = {old: COLUMNS_TO_KEEP[old] for old in existing_cols}
    df_reduced = df_reduced.rename(columns=rename_map)

    print(f"  - Reduced: {len(df_reduced)} rows, {len(df_reduced.columns)} columns")

    # Reorder columns in logical groups
    column_order = [
        # Identifikation
        'Match_Status', 'Product_ID', 'Product_Code', 'Product_Name', 'Modality',
        # Klassifikation
        'Classification', 'Product_Type', 'Therapeutic_Area', 'Current_Phase',
        'Project_Status', 'Lead_Indication',
        # Timeline
        'Expected_Launch_Year', 'Timeline_Variance_Days', 'Launch_Geography',
        # Manufacturing
        'Commercial', 'Development_Approach', 'Development_Site', 'Launch_Site',
        'Pharma_Form', 'Technology', 'Storage_Conditions',
        'DS_Volume_Category', 'DP_Volume_Category', 'Route_Of_Administration',
        # Suppliers
        'DS_Suppliers', 'DP_Suppliers', 'Device_Partners', 'Contact_Person',
        # Strategie
        'Strategic_Class', 'Strategic_Technology', 'Demand_Category', 'Peak_Demand_Range',
        # Risiken
        'Operational_Risks', 'Timeline_Risks', 'Supply_Chain_Risks',
        # Beschreibungen
        'Mechanism_Of_Action', 'Short_Description', 'Patient_Population',
        'Regulatory_Details', 'Submission_Status',
    ]

    # Only use columns that exist
    final_order = [c for c in column_order if c in df_reduced.columns]
    df_reduced = df_reduced[final_order]

    # Save
    print("\n[3/3] Saving reduced CSV...")
    df_reduced.to_csv('Pipeline_Intell_reduced.csv', index=False, sep=';')
    print(f"  - Saved to: Pipeline_Intell_reduced.csv")

    # Statistics
    print("\n" + "=" * 60)
    print("STATISTICS")
    print("=" * 60)
    print(f"  Columns removed: {len(df.columns) - len(df_reduced.columns)}")
    print(f"  Columns kept: {len(df_reduced.columns)}")
    print(f"  Reduction: {100 * (1 - len(df_reduced.columns) / len(df.columns)):.1f}%")

    print("\n  Column groups:")
    groups = {
        'Identifikation': ['Match_Status', 'Product_ID', 'Product_Code', 'Product_Name', 'Modality'],
        'Klassifikation': ['Classification', 'Product_Type', 'Therapeutic_Area', 'Current_Phase', 'Project_Status', 'Lead_Indication'],
        'Timeline': ['Expected_Launch_Year', 'Timeline_Variance_Days', 'Launch_Geography'],
        'Manufacturing': ['Commercial', 'Development_Approach', 'Development_Site', 'Launch_Site', 'Pharma_Form', 'Technology', 'Storage_Conditions', 'DS_Volume_Category', 'DP_Volume_Category', 'Route_Of_Administration'],
        'Suppliers': ['DS_Suppliers', 'DP_Suppliers', 'Device_Partners', 'Contact_Person'],
        'Strategie': ['Strategic_Class', 'Strategic_Technology', 'Demand_Category', 'Peak_Demand_Range'],
        'Risiken': ['Operational_Risks', 'Timeline_Risks', 'Supply_Chain_Risks'],
        'Beschreibungen': ['Mechanism_Of_Action', 'Short_Description', 'Patient_Population', 'Regulatory_Details', 'Submission_Status'],
    }

    for group, cols in groups.items():
        present = sum(1 for c in cols if c in df_reduced.columns)
        print(f"    {group}: {present}/{len(cols)}")

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
