# Database Schema Documentation
**Pipeline Intelligence - Simplified Manufacturing Challenges System**

> **Version**: 3.0 (Simplified Schema)
> **Last Updated**: December 2025

---

## Overview

This document describes the **simplified database schema** focused on managing manufacturing challenges across different modalities.

### Key Design Changes from Previous Versions

The schema has been **radically simplified**:

- **Removed**: `manufacturing_technologies` table
- **Removed**: `technology_modalities` junction table
- **Removed**: `product_to_technology` junction table
- **Removed**: `product_to_challenge` junction table
- **Simplified**: `manufacturing_challenges` → `challenges`
- **New**: `challenge_modality_details` for modality-specific scoring

---

## Core Tables

### 1. `challenges`

The base challenge entity with modality-agnostic information.

```sql
CREATE TABLE challenges (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    agnostic_description TEXT,      -- General description applicable to all modalities
    agnostic_root_cause TEXT,       -- General root cause analysis
    value_step VARCHAR(100),        -- 'Upstream', 'Downstream', etc.
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Purpose**: Defines a manufacturing challenge at a high level, without modality-specific details.

---

### 2. `modalities`

Product categories/types (e.g., ADC, Gene Therapy, Peptide).

```sql
CREATE TABLE modalities (
    modality_id SERIAL PRIMARY KEY,
    modality_name VARCHAR(255) UNIQUE NOT NULL,
    modality_category VARCHAR(255),
    label VARCHAR(255),
    short_description TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Purpose**: Defines product modalities/categories that have distinct manufacturing challenges.

---

### 3. `challenge_modality_details` (The Heart of the System)

Links challenges to modalities with **modality-specific scoring and details**.

```sql
CREATE TABLE challenge_modality_details (
    id SERIAL PRIMARY KEY,
    challenge_id INT NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
    modality_id INT NOT NULL REFERENCES modalities(modality_id) ON DELETE CASCADE,

    -- Modality-specific descriptions
    specific_description TEXT,
    specific_root_cause TEXT,

    -- Impact Scoring (1-5)
    impact_score INT CHECK (impact_score >= 1 AND impact_score <= 5),
    impact_details TEXT,

    -- Maturity Scoring (1-5)
    maturity_score INT CHECK (maturity_score >= 1 AND maturity_score <= 5),
    maturity_details TEXT,

    -- Future Trends
    trends_3_5_years TEXT,

    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(challenge_id, modality_id)
);
```

**Purpose**: The central junction table that captures how a challenge manifests differently across modalities.

---

## Relationships

```
challenges
    ├── id (PK)
    └── modality_details → [ChallengeModalityDetail]

modalities
    ├── modality_id (PK)
    ├── products → [Product]
    ├── process_templates → [ProcessTemplate]
    └── challenge_details → [ChallengeModalityDetail]

challenge_modality_details
    ├── id (PK)
    ├── challenge_id (FK → challenges.id)
    └── modality_id (FK → modalities.modality_id)
```

---

## Usage Examples

### Get all challenges for a modality with scores

```python
from models import ChallengeModalityDetail

details = ChallengeModalityDetail.query.filter_by(modality_id=1).all()
for d in details:
    print(f"{d.challenge.name}: Impact={d.impact_score}, Maturity={d.maturity_score}")
```

### Get all modality-specific details for a challenge

```python
from models import Challenge

challenge = Challenge.query.filter_by(name="Protein Aggregation").first()
for detail in challenge.modality_details:
    print(f"  {detail.modality.modality_name}: {detail.specific_description}")
```

---

## Score Definitions

### Impact Score (1-5)
| Score | Meaning |
|-------|---------|
| 1 | Minimal impact on cost/time |
| 2 | Low impact |
| 3 | Moderate impact |
| 4 | High impact |
| 5 | Critical - major cost/time driver |

### Maturity Score (1-5)
| Score | Meaning |
|-------|---------|
| 1 | No established solutions |
| 2 | Emerging solutions |
| 3 | Multiple viable approaches |
| 4 | Well-established solutions |
| 5 | Fully mature/commoditized |

---

## Migration Notes

To set up the new schema:

```bash
# 1. Drop existing database (DESTRUCTIVE!)
dropdb pipeline_intelligence

# 2. Create new database
createdb pipeline_intelligence

# 3. Generate new migration
flask db init
flask db migrate -m "Initial simplified schema"
flask db upgrade
```

---

## Removed Features

The following features from previous versions have been **removed**:

1. **Technology inheritance** - Products no longer inherit technologies
2. **Challenge inheritance via technologies** - Challenges are now directly linked to modalities
3. **Product-Challenge relationships** - Products inherit challenges only through their modality
4. **Three-tier filtering logic** - Simplified to single modality relationship

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 3.0 | Dec 2025 | Radical simplification - removed technologies, simplified challenges |
| 2.2 | Oct 2025 | Added raw_content to products |
| 2.1 | Oct 2025 | Added technology_modalities many-to-many |
| 2.0 | Oct 2025 | Added process templates, modality challenges |
