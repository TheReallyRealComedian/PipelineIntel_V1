# Database Schema Documentation
**Pipeline Intelligence - Manufacturing Process Modeling System**

> **Purpose**: This document explains HOW and WHY the database is structured to model pharmaceutical manufacturing complexity. It's written for developers, data analysts, and anyone trying to understand the system's design philosophy.

---

## Table of Contents

1. [Design Philosophy](#design-philosophy)
2. [Core Concepts Explained](#core-concepts-explained)
3. [Entity Reference Guide](#entity-reference-guide)
4. [Data Flow Examples](#data-flow-examples)
5. [Common Patterns](#common-patterns)
6. [Import Guidelines](#import-guidelines)
7. [Troubleshooting & FAQs](#troubleshooting--faqs)
8. [Appendix: Database Diagram Legend](#appendix-database-diagram-legend)
9. [Version History](#version-history)

---

## Design Philosophy

### The Central Problem

Pharmaceutical manufacturing is complex and hierarchical:
- Different **product types** (small molecules, antibodies, cell therapies) have fundamentally different manufacturing processes
- The same **process step** (like "lyophilization") has different requirements depending on what you're making
- Individual **products** may have unique requirements beyond their product type

Traditional flat database structures can't capture this complexity without massive redundancy.

### The Solution: Multi-Level Inheritance

This database uses a **three-tier inheritance system** to avoid redundancy while maintaining flexibility:

```
TIER 1: MODALITY (Category-Wide Requirements)
  "All Monoclonal Antibodies need cell culture"
  ↓ inherits to all products in this category
  
TIER 2: PROCESS TEMPLATE (Process-Specific Requirements)
  "Fed-Batch mAbs need Fed-Batch Bioreactors"
  "Perfusion mAbs need Perfusion Bioreactors"
  ↓ inherits to products using this specific process
  
TIER 3: PRODUCT (Asset-Specific Requirements)
  "This specific mAb also needs Novel Purification Tech"
  ↓ applies only to this product
```

**Result**: A complete picture = Inherited (Tier 1) + Inherited (Tier 2) + Specific (Tier 3)

---

## Core Concepts Explained

### 1. Modalities: Product Categories

**What they are**: High-level product classifications that share fundamental manufacturing characteristics.

**Examples**:
- Small Molecule (traditional chemical drugs)
- Monoclonal Antibody (protein-based biologics)
- Cell & Gene Therapy (living cell products)
- Viral Vector (gene delivery vehicles)

**Why they exist**: Products in the same modality share ~70-80% of their manufacturing requirements. Defining requirements at this level avoids repeating the same data for hundreds of products.

**Concrete Example**:
```
Modality: "Monoclonal Antibody"
  ├─ Requires: Cell Culture (Mammalian) [via modality_requirements]
  ├─ Requires: Protein Purification [via modality_requirements]
  ├─ Requires: Fill & Finish (Aseptic) [via modality_requirements]
  └─ Standard Challenges: High Titer Production, Aggregation Control [via modality_challenges]
  
All 150+ mAb products inherit these requirements automatically.
```

---

### 2. Process Templates: Manufacturing Blueprints

**What they are**: Standard process flows for a specific manufacturing approach within a modality. Products are now **explicitly linked** to process templates via the `process_template_id` foreign key.

**Why they exist**: Not all products in a modality are made the same way. Modern manufacturing offers choices (e.g., batch vs continuous), and these choices affect what capabilities you need. This explicit link is **required** for proper challenge and technology inheritance. Products without templates will not inherit template-based challenges or technologies.

**Concrete Example - The Fed-Batch vs Perfusion Scenario**:

Both are Monoclonal Antibodies, but different processes:

```
Modality: Monoclonal Antibody
  ├─ Template A: "Fed-Batch mAb Process" (Traditional)
  │   └─ Upstream Processing stage needs:
  │       - Fed-Batch Bioreactor Operation
  │       - 14-day culture cycle management
  │   
  └─ Template B: "Perfusion mAb Process" (Continuous)
      └─ Upstream Processing stage needs:
          - Perfusion Bioreactor Operation
          - Continuous harvest systems
          - Real-time analytics
```

**Without templates**: You'd have to manually specify bioreactor type for every single product.

**With templates**: Assign product to template once, inherits all stage-specific requirements.

---

### 3. Template Stages: The Bridge

**What they are**: Junction table linking templates to process stages, WITH process-specific metadata.

**Why they exist**: This is where the "magic" happens - same stage, different requirements per template.

**Schema**:
```python
template_id (FK → process_templates)
stage_id (FK → process_stages)
stage_order (sequence)
is_required (boolean)
base_capabilities (JSONB) # ← This is key!
```

**The `base_capabilities` Field Explained**:

This JSONB array stores capability names needed for THIS stage in THIS template.

**Concrete Example**:
```json
// Template: "Fed-Batch mAb Process"
// Stage: "Upstream Processing"
{
  "template_id": 1,
  "stage_id": 3,
  "stage_order": 1,
  "is_required": true,
  "base_capabilities": [
    "Fed-Batch Bioreactor Operation",
    "CHO Cell Culture",
    "Batch Monitoring Systems"
  ]
}

// Template: "Perfusion mAb Process"  
// Stage: "Upstream Processing" (SAME STAGE!)
{
  "template_id": 2,
  "stage_id": 3,
  "stage_order": 1,
  "is_required": true,
  "base_capabilities": [
    "Perfusion Bioreactor Operation",
    "CHO Cell Culture",
    "Continuous Process Analytics"
  ]
}
```

**Why not just put this in modality_requirements?** Because it varies by PROCESS, not by modality. Both are mAbs, but need different equipment.

---

### 4. Process Stages: Hierarchical Process Steps

**What they are**: Reusable, hierarchical definitions of manufacturing steps.

**Key Feature**: Self-referential hierarchy - stages can contain sub-stages to any depth.

**Schema**:
```python
stage_id (PK)
stage_name (unique)
parent_stage_id (FK → process_stages.stage_id) # Self-reference!
hierarchy_level (1=Phase, 2=Stage, 3=Operation, etc.)
stage_order (within parent)
```

**Concrete Example**:
```
Level 1 (Phase): "Upstream Processing"
  │
  ├─ Level 2 (Stage): "Cell Culture"
  │   ├─ Level 3 (Operation): "Seed Train"
  │   │   ├─ Level 4 (Activity): "Vial Thaw"
  │   │   └─ Level 4 (Activity): "Inoculation"
  │   │
  │   └─ Level 3 (Operation): "Production Bioreactor"
  │       ├─ Level 4 (Activity): "Media Preparation"
  │       └─ Level 4 (Activity): "Culture Monitoring"
  │
  └─ Level 2 (Stage): "Harvest"
      └─ Level 3 (Operation): "Centrifugation"
```

**Why hierarchical?** 
- High-level view: "How many products use Upstream Processing?" 
- Detailed view: "Which products need specific vial thaw protocols?"
- Same data structure, different query granularity.

---

### 5. Manufacturing Technologies: Specific Platforms

**What they are**: Specific techniques or equipment platforms used in manufacturing.

**CRITICAL UPDATE**: Technologies are now linked to modalities via a many-to-many relationship. A technology can be applicable to one, multiple, or zero modalities (making it "generic").

**Relationship Logic (Three-Tier Filtering)**:
When querying for a specific product, the system finds technologies that are:
1.  **Template-Specific**: Directly linked to the selected process template via `template_id`.
2.  **Modality-Specific**: Linked to the product's modality via the `technology_modalities` junction table.
3.  **Generic**: Not linked to **any** modality in the `technology_modalities` table.

**Schema**:
```python
# Schema for manufacturing_technologies
technology_id (PK)
technology_name (unique)
stage_id (FK → process_stages.stage_id)
template_id (FK → process_templates.template_id, nullable)
innovation_potential (text)
complexity_rating (1-10)
```

**Concrete Example**:
```json
{
  "technology_name": "Spray Drying",
  "stage_name": "Physical Processing & Drying",
  "modality_names": ["Small Molecule", "Peptides", "Oligonucleotides"],
  "innovation_potential": "High",
  "complexity_rating": 6
}
```

**Links to Products**: Many-to-many (`product_to_technology` table).

---

### 6. Manufacturing Challenges: Risks and Complexities

**What they are**: Difficulties, risks, or specialized requirements associated with manufacturing.

**Critical Design Decision**: Challenges link to TECHNOLOGIES, not directly to stages.

**Schema**:
```python
challenge_id (PK)
challenge_name (unique)
technology_id (FK → manufacturing_technologies)
severity_level ('minor', 'moderate', 'major', 'critical')
related_capabilities (JSONB)
```

**Why link to technology instead of stage?**
- Challenges are specific to HOW you do something, not WHERE.
- Example: "Sterility Assurance" is a challenge of "Aseptic Fill-Finish Technology", not just the "Fill & Finish" stage in general.

**Challenge → Stage Connection (Derived)**:
```
Challenge → Technology → Stage
```
You can always find which stage a challenge occurs in via the technology.

**Concrete Example**:
```json
{
  "challenge_name": "High Titer Production (>5g/L)",
  "technology_name": "Fed-Batch Bioreactor Operation",
  "severity_level": "major",
  "related_capabilities": [
    "Advanced Cell Line Development",
    "Process Optimization Expertise",
    "High-Density Culture Management"
  ]
}
```

**Links to Products**: Many-to-many with metadata (relationship_type: 'explicit' or 'excluded').

---

### 7. Products: The Central Hub

**What they are**: Individual pharmaceutical assets (drugs in development or production).

**Key Foreign Keys**:
```python
modality_id (FK → modalities)           # What TYPE of product
process_template_id (FK → process_templates)  # Which PROCESS it follows
```

**Why both?**
- `modality_id` defines what the product IS.
- `process_template_id` defines HOW it's made.
- The template MUST belong to the modality (enforced by application-level validation).

**Concrete Example**:
```json
{
  "product_code": "BI 1015550",
  "product_name": "Nerandomilast",
  "modality_name": "Small Molecule",
  "process_template_name": "Continuous Small Molecule Process",
  "base_technology": "Twin Screw Granulation",
  "dosage_form": "Tablet",
  "current_phase": "Registration"
}
```

**What this product inherits**:
1. Modality requirements (all small molecules need X).
2. Template stage capabilities (continuous process needs Y).
3. Plus its own specific requirements (Nerandomilast also needs Z).

---

## Entity Reference Guide

### Foundation Entities

#### Modalities
```python
# Schema
modality_id (PK)
modality_name (unique) # "Monoclonal Antibody", "Small Molecule"
modality_category # "Biologics", "NCE"
short_description # Brief overview
description # Detailed explanation
standard_challenges (JSONB) # DEPRECATED - kept for reference only
created_at
```

**Relationships**:
- Has many: Products (`products.modality_id`)
- Has many: Process Templates (`process_templates.modality_id`)
- Has many: Modality Requirements (to Capabilities)
- Has many: Modality-Challenge Links (many-to-many via `modality_challenges`)
- Has many: Technology Links (many-to-many via `technology_modalities`)

**JSON Import Example**:
```json
{
  "modality_name": "Monoclonal Antibody",
  "modality_category": "Biologics",
  "short_description": "Therapeutic antibodies targeting specific antigens",
  "description": "Well-established biologics class with proven CHO-based manufacturing processes..."
}
```

---

#### Process Stages (Hierarchical)
```python
# Schema
stage_id (PK)
stage_name (unique) # "Upstream Processing", "Cell Culture"
stage_category # "Production", "Quality Control"
parent_stage_id (FK → process_stages.stage_id) # NULL for top-level
hierarchy_level # 1=Phase, 2=Stage, 3=Operation
stage_order # Order within siblings
```

**Relationships**:
- Has many: Child Stages (self-referential)
- Has many: Technologies (`technologies.stage_id`)
- Has many: Template Stage Links (`template_stages.stage_id`)
- Belongs to: Parent Stage (self-referential, nullable)

**JSON Import Examples**:

Level 1 - Phase:
```json
{
  "stage_name": "Upstream Processing",
  "stage_category": "Production",
  "hierarchy_level": 1,
  "stage_order": 1,
  "short_description": "Cell culture and biomass production"
}
```

Level 2 - Stage (child):
```json
{
  "stage_name": "Cell Culture",
  "stage_category": "Production",
  "hierarchy_level": 2,
  "stage_order": 1,
  "parent_stage_name": "Upstream Processing",
  "short_description": "Main bioreactor operation"
}
```

---

#### Manufacturing Capabilities
```python
# Schema
capability_id (PK)
capability_name (unique) # "Fed-Batch Bioreactor Operation"
capability_category # "Biologics Production"
approach_category # "Upstream"
description
complexity_weight (1-10) # Difficulty/cost indicator
```

**Relationships**:
- Referenced by: Modality Requirements (pattern level)
- Referenced by: Product Requirements (specific level)
- Referenced by: Template Stages (via `base_capabilities` JSONB)
- Referenced by: Entity Capabilities (what facilities can do)

**JSON Import Example**:
```json
{
  "capability_name": "Perfusion Bioreactor Operation",
  "capability_category": "Biologics Production",
  "approach_category": "Upstream - Continuous",
  "description": "Continuous cell culture with constant harvest and media perfusion",
  "complexity_weight": 8
}
```

---

### Process Flow Entities

#### Process Templates
```python
# Schema
template_id (PK)
modality_id (FK → modalities.modality_id)
template_name (unique) # "Fed-Batch mAb Process"
description
created_at
```

**Relationships**:
- Belongs to: Modality (`modality_id`)
- Has many: Template Stages (junction table)
- Has many: Products using this template (`products.process_template_id`)

**JSON Import Example**:
```json
{
  "template_name": "Fed-Batch Monoclonal Antibody Process",
  "modality_name": "Monoclonal Antibody",
  "description": "Standard CHO cell-based production using fed-batch bioreactors",
  "stages": [
    {
      "stage_name": "Upstream Processing",
      "stage_order": 1,
      "is_required": true,
      "base_capabilities": [
        "Fed-Batch Bioreactor Operation",
        "CHO Cell Culture",
        "Batch Monitoring Systems"
      ]
    },
    {
      "stage_name": "Downstream Processing",
      "stage_order": 2,
      "is_required": true,
      "base_capabilities": [
        "Protein A Chromatography",
        "Viral Inactivation",
        "Ultrafiltration/Diafiltration"
      ]
    }
  ]
}
```

---

#### Template Stages (Junction)
```python
# Schema
template_id (PK, FK)
stage_id (PK, FK)
stage_order # Sequence in this template
is_required (boolean)
base_capabilities (JSONB) # Array of capability names
```

**Purpose**: Links templates to stages with process-specific metadata.

**The `base_capabilities` field**: Stores capability names needed for this stage WHEN using this template.

**Relationships**:
- Belongs to: Process Template
- Belongs to: Process Stage

---

### Manufacturing Context Entities

#### Manufacturing Technologies
```python
# Schema
technology_id (PK)
technology_name (unique) # "Twin Screw Granulation"
stage_id (FK → process_stages.stage_id)
template_id (FK → process_templates.template_id, nullable)
innovation_potential (text)
complexity_rating (1-10)
```

**Relationships**:
- Belongs to: Process Stage (primary stage of use)
- Belongs to: Process Template (optional, via `template_id` FK)
- Has many: Challenges (`challenges.technology_id`)
- Links to: Products (many-to-many via `product_to_technology`)
- **Links to: Modalities (many-to-many via `technology_modalities`)**

**JSON Import Examples (Current Format)**:
```json
// Multiple modalities
{
  "technology_name": "Spray Drying",
  "stage_name": "Physical Processing & Drying",
  "modality_names": ["Small Molecule", "Peptides", "Oligonucleotides"],
  "complexity_rating": 6
}

// Generic (applies to all modalities)
{
  "technology_name": "Track & Trace Serialization",
  "stage_name": "Secondary Packaging & Serialization",
  "modality_names": [],
  "complexity_rating": 3
}
```

---

#### Technology-Modality Junction Table
```python
# Schema for technology_modalities (NEW in v2.1)
technology_id (PK, FK → manufacturing_technologies.technology_id)
modality_id (PK, FK → modalities.modality_id)
notes (Text, nullable)
created_at (Timestamp with timezone)
```

**Purpose**: Enables the many-to-many relationship between `manufacturing_technologies` and `modalities`.

**Inheritance Logic**:
When determining which technologies apply to a product:
1.  **Template-Specific**: Technologies where `template_id` matches the product's `process_template_id`.
2.  **Modality-Specific**: Technologies linked to the product's modality via this junction table.
3.  **Generic**: Technologies with NO entries in `technology_modalities` (apply to all modalities).

**JSON Import**: Automatically populated when importing technologies with the `modality_names` array.

---

#### Manufacturing Challenges
```python
# Schema
challenge_id (PK)
challenge_name (unique)
challenge_category # "Safety", "Quality", "Scale-up"
technology_id (FK → manufacturing_technologies.technology_id)
severity_level # 'minor', 'moderate', 'major', 'critical'
related_capabilities (JSONB) # Capabilities that help address this
```

**Relationships**:
- Belongs to: Technology (where it occurs)
- Links to: Products (many-to-many with `relationship_type`)
- Links to: Modalities (many-to-many via `modality_challenges`)

**Product Linking Logic**:
- `relationship_type = 'explicit'`: Product faces this challenge.
- `relationship_type = 'excluded'`: Product explicitly DOESN'T face this (overrides inheritance).

**JSON Import Example**:
```json
{
  "challenge_name": "Cell Line Stability at High Density",
  "challenge_category": "Production",
  "technology_name": "Perfusion Bioreactor System",
  "severity_level": "major",
  "related_capabilities": [
    "Advanced Cell Line Engineering",
    "Real-Time Cell Viability Monitoring"
  ],
  "product_codes": ["BI 456789"] # Products that face this
}
```
---

#### Modality-Challenge Junction Table
```python
# Schema for modality_challenges (NEW in v2.0)
modality_id (PK, FK → modalities.modality_id)
challenge_id (PK, FK → manufacturing_challenges.challenge_id)
is_typical (Boolean, default=True)
notes (Text, nullable)
created_at (Timestamp with timezone)
```

**Purpose**: Normalizes the relationship between modalities and their standard challenges. Replaces the JSONB `standard_challenges` field in the `modalities` table.

**Why the Change**: Enables proper querying, filtering, and relationship tracking. The JSONB array was difficult to query efficiently.

**Data Migration**: The migration automatically converted existing `standard_challenges` JSONB data to normalized table entries.

---

### Product Entities

#### Products
```python
# Schema (Key Fields)
product_id (PK)
product_code (unique)
product_name
# ... many more fields, see comprehensive list below

# Foreign Keys
modality_id (FK → modalities.modality_id)
process_template_id (FK → process_templates.template_id)

# Comprehensive Field List
product_type, short_description, description, base_technology, mechanism_of_action, dosage_form, therapeutic_area, current_phase, project_status, lead_indication, expected_launch_year, lifecycle_indications (JSONB), regulatory_designations (JSONB), manufacturing_strategy, manufacturing_sites (JSONB), volume_forecast (JSONB), primary_packaging, route_of_administration, biel_category, granulation_technology, submission_status, submission_date (Date), approval_date (Date), launch_geography, regulatory_details (JSONB), ppq_status, ppq_completion_date (Date), ppq_details (JSONB), timeline_variance_days, timeline_variance_baseline, critical_path_item, ds_volume_category, dp_volume_category, ds_suppliers (JSONB), dp_suppliers (JSONB), device_partners (JSONB), operational_risks (JSONB), timeline_risks (JSONB), supply_chain_risks (JSONB), clinical_trials (JSONB), patient_population, development_program_name
raw_content (Text, nullable)  # Unstructured data storage
```

**Critical Foreign Keys**:
- `modality_id`: Links to category (WHAT it is).
- `process_template_id`: Links to process (HOW it's made).

**Validation Rule**: If both are set, the template MUST belong to the modality.

**Relationships**:
- Belongs to: Modality
- Belongs to: Process Template (nullable)
- Has many: Indications, Product Requirements, Product Process Overrides
- Links to: Challenges (many-to-many with metadata)
- Links to: Technologies (many-to-many)

**JSON Import Example**:
```json
{
  "product_code": "BI 456789",
  "product_name": "Example mAb",
  "modality_name": "Monoclonal Antibody",
  "process_template_name": "Perfusion mAb Process",
  "product_type": "NBE",
  "therapeutic_area": "Oncology",
  "current_phase": "Phase 2"
}
```

---

### Requirements System (Dual-Path)

#### Modality Requirements (Pattern Level)
```python
# Schema
modality_id (PK, FK)
required_capability_id (PK, FK)
requirement_level # 'essential', 'preferred', 'optional'
is_critical (boolean)
timeline_context # When it's needed
```

**Purpose**: Define standard capabilities for ALL products in a modality.

---

#### Product Requirements (Specific Level)
```python
# Schema
product_id (PK, FK)
required_capability_id (PK, FK)
requirement_level # 'essential', 'preferred', 'optional'
is_critical (boolean)
timeline_needed (date)
notes
```

**Purpose**: Define product-specific capabilities (additions or overrides).

---

## Data Flow Examples

### Example 1: Finding Relevant Technologies for a Modality/Template

**Scenario**: Find all technologies for a "Monoclonal Antibody" modality using the "Fed-Batch mAb Process" template.

**Query Logic**:
The application runs a query equivalent to:
```sql
SELECT * FROM manufacturing_technologies tech
WHERE 
    -- 1. Must be in a stage used by the template
    tech.stage_id IN (SELECT stage_id FROM template_stages WHERE template_id = [template_id])
AND (
    -- 2. OR Template-specific match
    tech.template_id = [template_id]
    
    -- 3. OR Modality-specific match (via junction table)
    OR tech.technology_id IN (
        SELECT technology_id FROM technology_modalities WHERE modality_id = [modality_id]
    )
    
    -- 4. OR Generic (no modality links at all)
    OR NOT EXISTS (
        SELECT 1 FROM technology_modalities tm WHERE tm.technology_id = tech.technology_id
    )
);
```
This ensures the correct three-tier filtering is applied.

---

### Example 2: Challenge Inheritance

**Scenario**: A product inherits challenges from three sources.

```python
# 1. MODALITY CHALLENGES (via modality_challenges table)
modality_challenges = db.session.query(ManufacturingChallenge)\
    .join(ModalityChallenge)\
    .filter(ModalityChallenge.modality_id == product.modality_id)\
    .all()

# 2. TECHNOLOGY CHALLENGES (via inherited technologies using three-tier logic)
inherited_technologies = product.get_inherited_technologies()
# This method implements the three-tier inheritance:
#   - Template-specific (template_id match)
#   - Modality-specific (via technology_modalities)
#   - Generic (no modality links)
technology_challenges = [ch for tech in inherited_technologies 
                        for ch in tech.challenges]

# 3. EXPLICIT PRODUCT CHALLENGES
explicit_challenges = product.challenges.filter_by(relationship_type='explicit')

# MINUS: EXCLUDED CHALLENGES
excluded_challenges = product.challenges.filter_by(relationship_type='excluded')

# Final effective challenges = (Modality + Technology - Excluded) + Explicit
```

---

## Common Patterns

### Pattern 1: Adding a New Modality
1.  Create the modality.
2.  Define modality requirements and modality-challenge links.
3.  Create at least one process template for it.
4.  Define template stages with `base_capabilities`.
5.  Products can now use this modality + template.

---

### Pattern 2: Process Variations
When a modality has multiple process approaches, create different templates for the same modality. Products can then choose which template to follow based on their manufacturing approach.

---

### Pattern 3: Challenge Management
- Challenges are inherited from a product's modality and its inherited technologies.
- A product can `exclude` an inherited challenge it doesn't face.
- A product can `explicitly` add a challenge that isn't inherited.

---

### Pattern 4: Generic vs. Specific Technologies
- A technology linked to one or more modalities (e.g., "CAR-T Expansion") will only be available to products of those modalities.
- A technology linked to **zero** modalities (e.g., "Track & Trace") is considered generic and is available to all products.

---

### Pattern 5: Three-Tier Technology Filtering
When querying technologies for a product, use the three-tier logic:
```python
from sqlalchemy import or_, not_, exists
from ..models import TechnologyModality

# Get technologies for a specific product
technologies = db.session.query(ManufacturingTechnology).filter(
    ManufacturingTechnology.stage_id.in_(template_stage_ids),
    or_(
        # Tier 1: Template-specific
        ManufacturingTechnology.template_id == product.process_template_id,
        
        # Tier 2: Modality-specific
        ManufacturingTechnology.technology_id.in_(
            db.session.query(TechnologyModality.technology_id)
            .filter(TechnologyModality.modality_id == product.modality_id)
        ),
        
        # Tier 3: Generic (no modality links)
        ~exists().where(
            TechnologyModality.technology_id == ManufacturingTechnology.technology_id
        )
    )
).all()
```

---

## Import Guidelines

### Import Order (Critical!)

Dependencies must be imported in this order:

1.  **Modalities**
2.  **Process Stages**
3.  **Manufacturing Capabilities**
4.  **Manufacturing Technologies** (with `modality_names` array) - auto-creates `technology_modalities` entries.
5.  **Manufacturing Challenges** (references technologies)
6.  **Modality-Challenge Links** - populates `modality_challenges` junction table.
7.  **Process Templates** (references modalities + stages)
8.  **Products** (MUST include `process_template_name`) - auto-creates `product_to_technology` entries if `technology_names` is present.

> **IMPORTANT**: As of v2.0, products MUST have a `process_template_name` in import JSON to inherit template-based challenges and technologies correctly. Products without templates will only inherit modality-level requirements and generic technologies.

---

## Troubleshooting & FAQs

### Q: Why can't I add a check constraint for template-modality matching?
**A**: PostgreSQL doesn't support subqueries in CHECK constraints. Validation is handled at the application level via the `@validates` decorator in the `Product` model.

### Q: Why don't I see any challenges or technologies for my product?
**A**: Most likely causes:
1.  **Missing `process_template_id`**: The product doesn't have a `process_template_name` in the import. Without this, it cannot inherit template-based challenges or technologies.
2.  **No modality links**: The technologies are not linked to your product's modality via the `technology_modalities` table, and they are not generic.
3.  **Stage mismatch**: The technologies are linked to stages that are not part of your product's process template.

### Q: Can a technology belong to multiple modalities?
**A**: Yes. As of v2.1, technologies use a **many-to-many relationship** with modalities via the `technology_modalities` junction table. A technology can be linked to:
-   **One modality**: Single entry in junction table.
-   **Multiple modalities**: Multiple entries in junction table.
-   **No modalities (Generic)**: Zero entries in junction table → applies to ALL modalities.

### Q: What's the difference between the old `modality_id` FK and the new `technology_modalities` table?
**A**: The old foreign key limited each technology to ONE modality. The new junction table allows for:
-   **Flexibility**: One technology can serve multiple modalities (e.g., "Spray Drying" for Small Molecules AND Peptides).
-   **Generic technologies**: Technologies with no entries in the junction table apply to ALL modalities.
-   **Better querying**: You can easily filter technologies by modality membership.

---

## Appendix: Database Diagram Legend

> **Note**: You can view an interactive, auto-generated database diagram in the application by navigating to **Settings → Database Schema**. The diagram shows all current tables, relationships, and can be downloaded in multiple formats.

**Key Relationships**:
```
Products (central hub)
  ├─── modality_id → Modalities
  ├─── process_template_id → Process Templates
  ├─── many-to-many → Technologies (via product_to_technology)
  ├─── many-to-many → Challenges (via product_to_challenge)
  └─── one-to-many → Product Requirements

Modalities
  ├─── one-to-many → Products
  ├─── one-to-many → Process Templates
  ├─── many-to-many → Challenges (via modality_challenges)
  └─── many-to-many → Technologies (via technology_modalities)

Manufacturing Technologies
  ├─── stage_id → Process Stages
  ├─── template_id → Process Templates (nullable)
  ├─── many-to-many → Modalities (via technology_modalities)
  ├─── many-to-many → Products (via product_to_technology)
  └─── one-to-many → Challenges

Manufacturing Challenges
  ├─── technology_id → Technologies
  ├─── many-to-many → Modalities (via modality_challenges)
  └─── many-to-many → Products (via product_to_challenge)
```

---

## Version History
- **v2.2** (2025-10-17): Added `raw_content` field to products table for storing unstructured data.
- **v2.1** (2025-10-15): Implemented many-to-many relationship for `Manufacturing Technologies` and `Modalities` via `technology_modalities` junction table.
- **v2.0** (2025-10-05): Added `process_template_id` to products, created `modality_challenges` junction table, clarified three-tier inheritance, and deprecated `primary_stage_id` on challenges.
- **v1.0** (2025-07-15): Initial schema design.

---

**Questions?** Check the code comments in `backend/models.py` or the migration files in `migrations/versions/` for implementation details.