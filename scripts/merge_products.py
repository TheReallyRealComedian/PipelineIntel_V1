#!/usr/bin/env python3
"""
Merge export.csv and products_summary_comprehensive.csv based on product codes/names.
Handles line extensions and provides matching status indicators.
"""

import pandas as pd
import re
from collections import defaultdict


def normalize_bi_code(s):
    """Normalize a BI code string for matching."""
    if pd.isna(s) or s == "(Blank)" or not s.strip():
        return None

    s = str(s).strip()

    # Fix common typos: Bl/BL (lowercase L looks like I) -> BI
    # This handles "Bl 3720931" where someone typed lowercase L instead of I
    s = re.sub(r'^B[lL]\s*', 'BI ', s, flags=re.IGNORECASE)

    s = s.upper()

    # Normalize spacing: BI771716 -> BI 771716
    s = re.sub(r'^BI\s*(\d)', r'BI \1', s)

    return s


def extract_base_code(code):
    """Extract base product code without line extension suffix."""
    if not code:
        return None

    # First normalize to handle Bl -> BI typos
    normalized = str(code).strip()
    normalized = re.sub(r'^B[lL]\s*', 'BI ', normalized, flags=re.IGNORECASE)

    # Match BI followed by digits, ignoring any suffix like _BC1, _PED, etc.
    match = re.match(r'^(BI\s*\d+)', normalized, re.IGNORECASE)
    if match:
        return normalize_bi_code(match.group(1))
    return None


def parse_year(year_str):
    """Parse year string to sortable integer. Unknown/empty -> 9999."""
    if pd.isna(year_str) or str(year_str).strip().lower() in ['unknown', '', 'nan']:
        return 9999
    try:
        return int(year_str)
    except (ValueError, TypeError):
        return 9999


def is_valid_product_entry(row, product_col):
    """Check if a row has a valid product entry (not just metadata)."""
    val = row.get(product_col, "")
    if pd.isna(val):
        return False
    val = str(val).strip()
    return val and val != "(Blank)"


def split_multi_products(product_str):
    """Split a string containing multiple products separated by semicolons."""
    if pd.isna(product_str) or not str(product_str).strip():
        return []

    parts = str(product_str).split(';')
    return [p.strip() for p in parts if p.strip() and p.strip() != "(Blank)"]


def main():
    print("=" * 60)
    print("CSV Merger: export.csv + products_summary_comprehensive.csv")
    print("=" * 60)

    # Load CSVs
    print("\n[1/5] Loading CSV files...")
    export_df = pd.read_csv('export.csv', delimiter=';', dtype=str)
    ps_df = pd.read_csv('products_summary_comprehensive.csv', delimiter=';', dtype=str)

    print(f"  - export.csv: {len(export_df)} rows, {len(export_df.columns)} columns")
    print(f"  - products_summary_comprehensive.csv: {len(ps_df)} rows, {len(ps_df.columns)} columns")

    # Prepare column names for output (prefix to avoid collisions)
    export_cols = [f"export_{c}" for c in export_df.columns]
    ps_cols = [f"ps_{c}" for c in ps_df.columns]

    # Build lookup structures for products_summary
    print("\n[2/5] Building lookup structures...")

    # Dict: normalized base code -> list of (full_code, row_index, year)
    code_to_ps = defaultdict(list)
    # Dict: normalized name -> list of (code, row_index)
    name_to_ps = defaultdict(list)

    for idx, row in ps_df.iterrows():
        code = row.get('Product Code', '')
        name = row.get('Product Name', '')
        year = parse_year(row.get('Expected Launch Year', ''))

        # Index by base code
        base_code = extract_base_code(code)
        if base_code:
            code_to_ps[base_code].append({
                'full_code': code,
                'row_idx': idx,
                'year': year,
                'is_line_extension': '_' in str(code)
            })

        # Index by name (normalized)
        if name and str(name).strip() and str(name).strip() != "(Blank)":
            norm_name = str(name).strip().upper()
            name_to_ps[norm_name].append({
                'code': code,
                'base_code': base_code,
                'row_idx': idx,
                'year': year
            })

    print(f"  - Indexed {len(code_to_ps)} unique base codes")
    print(f"  - Indexed {len(name_to_ps)} unique product names")

    # Sort line extensions by year within each base code
    for base_code in code_to_ps:
        code_to_ps[base_code].sort(key=lambda x: x['year'])

    # Perform matching
    print("\n[3/5] Matching products...")

    results = []
    skipped_rows = []
    multi_product_resolutions = []
    matched_ps_indices = set()

    product_col = 'Product (name/code)'

    for exp_idx, exp_row in export_df.iterrows():
        # Skip metadata rows
        if not is_valid_product_entry(exp_row, product_col):
            skipped_rows.append(exp_idx)
            continue

        product_str = exp_row[product_col]
        products = split_multi_products(product_str)

        if len(products) > 1:
            multi_product_resolutions.append({
                'row': exp_idx,
                'original': product_str,
                'split_into': products
            })

        for product in products:
            # Try to match by code first
            normalized = normalize_bi_code(product)
            base_code = extract_base_code(product) if normalized else None

            matched = False

            # Match by code
            if base_code and base_code in code_to_ps:
                entries = code_to_ps[base_code]
                for i, entry in enumerate(entries):
                    ps_row = ps_df.iloc[entry['row_idx']]
                    matched_ps_indices.add(entry['row_idx'])

                    # First entry (earliest year) = MATCH, rest = MATCH_LE
                    if i == 0:
                        status = "MATCH"
                    else:
                        status = "MATCH_LE"

                    result = {'Match_Status': status}
                    for col, new_col in zip(export_df.columns, export_cols):
                        result[new_col] = exp_row[col]
                    for col, new_col in zip(ps_df.columns, ps_cols):
                        result[new_col] = ps_row[col]
                    results.append(result)

                matched = True

            # If no code match, try by name
            if not matched:
                norm_name = str(product).strip().upper()
                if norm_name in name_to_ps:
                    # Group by base code and sort
                    name_entries = name_to_ps[norm_name]
                    by_base = defaultdict(list)
                    for entry in name_entries:
                        by_base[entry['base_code'] or entry['code']].append(entry)

                    for base, entries in by_base.items():
                        entries.sort(key=lambda x: x['year'])
                        for i, entry in enumerate(entries):
                            ps_row = ps_df.iloc[entry['row_idx']]
                            matched_ps_indices.add(entry['row_idx'])

                            if i == 0:
                                status = "MATCH"
                            else:
                                status = "MATCH_LE"

                            result = {'Match_Status': status}
                            for col, new_col in zip(export_df.columns, export_cols):
                                result[new_col] = exp_row[col]
                            for col, new_col in zip(ps_df.columns, ps_cols):
                                result[new_col] = ps_row[col]
                            results.append(result)

                    matched = True

            # No match found
            if not matched:
                result = {'Match_Status': 'NO_MATCH_export'}
                for col, new_col in zip(export_df.columns, export_cols):
                    result[new_col] = exp_row[col]
                for col, new_col in zip(ps_df.columns, ps_cols):
                    result[new_col] = ""
                results.append(result)

    # Add unmatched products_summary entries
    print("\n[4/5] Adding unmatched products_summary entries...")

    for ps_idx, ps_row in ps_df.iterrows():
        if ps_idx not in matched_ps_indices:
            result = {'Match_Status': 'NO_MATCH_ps'}
            for col, new_col in zip(export_df.columns, export_cols):
                result[new_col] = ""
            for col, new_col in zip(ps_df.columns, ps_cols):
                result[new_col] = ps_row[col]
            results.append(result)

    # Create output DataFrame
    output_df = pd.DataFrame(results)

    # Reorder columns: Match_Status first, then export columns, then ps columns
    col_order = ['Match_Status'] + export_cols + ps_cols
    output_df = output_df[col_order]

    # Save output
    print("\n[5/5] Saving merged data...")
    output_df.to_csv('merged_products.csv', index=False, sep=';')
    print(f"  - Saved to: merged_products.csv")
    print(f"  - Total rows: {len(output_df)}")

    # Statistics
    print("\n" + "=" * 60)
    print("STATISTICS")
    print("=" * 60)

    status_counts = output_df['Match_Status'].value_counts()
    for status in ['MATCH', 'MATCH_LE', 'NO_MATCH_export', 'NO_MATCH_ps']:
        count = status_counts.get(status, 0)
        print(f"  {status}: {count}")

    print(f"\n  Skipped metadata rows from export: {len(skipped_rows)}")
    if skipped_rows:
        print(f"    Row indices: {skipped_rows[:5]}{'...' if len(skipped_rows) > 5 else ''}")

    print(f"\n  Multi-product resolutions: {len(multi_product_resolutions)}")
    for mp in multi_product_resolutions[:3]:
        print(f"    Row {mp['row']}: '{mp['original']}' -> {mp['split_into']}")
    if len(multi_product_resolutions) > 3:
        print(f"    ... and {len(multi_product_resolutions) - 3} more")

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
