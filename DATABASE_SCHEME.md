# Database Schema Documentation

## Overview

The Pipeline Intelligence database is designed to model pharmaceutical manufacturing complexity across multiple dimensions: products, modalities, processes, capabilities, and manufacturing networks. The schema follows a **hub-and-spoke** architecture with products at the center, connected to various reference entities.

## Core Design Principles

### 1. **Hierarchical Modeling**
Process stages support unlimited nesting (Phase → Stage → Operation → Detail) through self-referential relationships.

### 2. **Dual-Path Pattern**
Critical relationships exist at both **pattern level** (modality-based inheritance) and **specific level** (product overrides):
- Modality Requirements + Product Requirements
- Stage-based Challenges + Product-tagged Challenges

### 3. **Name-Based Imports**
All foreign key relationships can be specified by name in JSON imports (e.g., `"modality_name": "Monoclonal Antibody"` instead of `"modality_id": 5`).

### 4. **Flexible Categorization**
Entities use category fields for grouping while maintaining flexibility (no rigid enum constraints).

---

## Entity Reference Guide

### Foundation Entities

#### **Modalities**
Defines high-level product categories (e.g., Small Molecule, mAb, CAR-T).

**Schema:**
```python
modality_id (PK)
modality_name (unique)
modality_category
short_description
description
standard_challenges (JSONB)
created_at
```

**JSON Import Example:**
```json
{
  "modality_name": "Monoclonal Antibody",
  "modality_category": "Biologics",
  "short_description": "Standard therapeutic antibodies targeting specific antigens",
  "description": "Well-established biologics class with proven manufacturing processes...",
  "standard_challenges": ["High Titer Production", "Downstream Purification", "Cold Chain"]
}
```

**Relationships:**
- Has many: Products
- Has many: Process Templates
- Has many: Modality Requirements (to Capabilities)

---

#### **Process Stages** (Hierarchical)
Represents manufacturing process steps with unlimited nesting depth.

**Schema:**
```python
stage_id (PK)
stage_name (unique)
stage_category
short_description
description
parent_stage_id (FK → process_stages.stage_id)  # Self-referential
hierarchy_level (1=Phase, 2=Stage, 3=Operation, etc.)
stage_order (order within parent level)
```

**JSON Import Examples:**

**Level 1 - Phase:**
```json
{
  "stage_name": "Chemical Synthesis",
  "stage_category": "API Production",
  "hierarchy_level": 1,
  "stage_order": 1,
  "short_description": "Complete chemical synthesis and API production"
}
```

**Level 2 - Stage (child of phase):**
```json
{
  "stage_name": "Raw Material Management",
  "stage_category": "Upstream",
  "hierarchy_level": 2,
  "stage_order": 1,
  "parent_stage_name": "Chemical Synthesis",
  "short_description": "Qualification and management of starting materials"
}
```

**Level 3 - Operation (child of stage):**
```json
{
  "stage_name": "Sourcing and Qualification",
  "stage_category": "Quality Assurance",
  "hierarchy_level": 3,
  "stage_order": 1,
  "parent_stage_name": "Raw Material Management",
  "short_description": "Vendor qualification and material testing protocols"
}
```

**Relationships:**
- Has many: Technologies (primary_stage_id)
- Has many: Challenges (primary_stage_id)
- Has many: Children (self-referential)
- Belongs to: Parent Stage (self-referential)

---

#### **Manufacturing Capabilities**
Specific skills/technologies required for production.

**Schema:**
```python
capability_id (PK)
capability_name (unique)
capability_category
approach_category
description
complexity_weight (1-10 scale)
created_at
```

**JSON Import Example:**
```json
{
  "capability_name": "Cell Culture (Mammalian)",
  "capability_category": "Biologics Production",
  "approach_category": "Upstream",
  "description": "Mammalian cell culture in bioreactors for protein expression",
  "complexity_weight": 7
}
```

**Relationships:**
- Referenced by: Modality Requirements
- Referenced by: Product Requirements
- Referenced by: Entity Capabilities
- Referenced by: Challenges (via JSONB related_capabilities)

---

### Manufacturing Context Entities

#### **Manufacturing Technologies**
Specific platforms or techniques used in manufacturing.

**Schema:**
```python
technology_id (PK)
technology_name (unique)
short_description
description
stage_id (FK → process_stages.stage_id)
innovation_potential
complexity_rating
```

**JSON Import Example:**
```json
{
  "technology_name": "Twin Screw Granulation (TSG)",
  "stage_name": "Granulation",
  "short_description": "Continuous granulation process",
  "description": "Advanced continuous manufacturing technology...",
  "innovation_potential": "High - enables continuous manufacturing paradigm",
  "complexity_rating": 7
}
```

**Relationships:**
- Belongs to: Process Stage (stage_id)
- Links to: Products (many-to-many via product_to_technology)

---

#### **Manufacturing Challenges**
Risks, difficulties, or specialized requirements.

**Schema:**
```python
challenge_id (PK)
challenge_name (unique)
challenge_category
short_description
explanation
related_capabilities (JSONB - array of capability names)
primary_stage_id (FK → process_stages.stage_id)
severity_level ('minor', 'moderate', 'major', 'critical')
```

**JSON Import Example:**
```json
{
  "challenge_name": "BSL-2+ Containment Facilities Required",
  "challenge_category": "Safety & Containment",
  "short_description": "Requires specialized biosafety infrastructure",
  "explanation": "Live viral vectors require BSL-2+ facilities with negative pressure...",
  "primary_stage_name": "Upstream Processing",
  "severity_level": "critical",
  "related_capabilities": ["BSL-2+ Containment", "Viral Vector Handling"],
  "product_codes": ["BI 3720931", "BI 1831169"]
}
```

**Relationships:**
- Belongs to: Process Stage (primary_stage_id)
- Links to: Products (many-to-many via product_to_challenge)

---

### Product Entities

#### **Products**
Central entity representing pharmaceutical assets.

**Schema:**
```python
product_id (PK)
product_code (unique)
product_name
product_type
short_description
description
base_technology
mechanism_of_action
dosage_form
therapeutic_area
current_phase
project_status
lead_indication
expected_launch_year
lifecycle_indications (JSONB)
regulatory_designations (JSONB)
manufacturing_strategy
manufacturing_sites (JSONB)
volume_forecast (JSONB)
modality_id (FK → modalities.modality_id)
created_at
updated_at
```

**JSON Import Example:**
```json
{
  "product_code": "BI 1015550",
  "product_name": "Nerandomilast",
  "modality_name": "Small Molecule",
  "product_type": "NCE",
  "short_description": "PDE4B inhibitor for pulmonary fibrosis",
  "base_technology": "Twin Screw Granulation (TSG)",
  "mechanism_of_action": "Preferential PDE4B inhibitor halting disease progression in IPF",
  "dosage_form": "Tablet",
  "therapeutic_area": "Respiratory",
  "current_phase": "Registration",
  "project_status": "On Track",
  "lead_indication": "Idiopathic Pulmonary Fibrosis (IPF)",
  "expected_launch_year": 2025,
  "lifecycle_indications": [
    {"phase": "Phase 3", "indication": "Progressive Pulmonary Fibrosis (PPF)"},
    {"phase": "Phase 2", "indication": "Systemic Sclerosis (SSc)"}
  ],
  "regulatory_designations": ["Breakthrough Therapy", "Orphan Drug"],
  "manufacturing_strategy": "Internal",
  "manufacturing_sites": {
    "DP": ["ING_SoL", "Koropi"],
    "DS": ["ING"]
  },
  "volume_forecast": {
    "DP": "Medium (10-100M PCS)",
    "DS": "Low (10-1000 kg)"
  }
}
```

**Relationships:**
- Belongs to: Modality (modality_id)
- Has many: Indications
- Has many: Product Supply Chain entries
- Has many: Product Requirements (to Capabilities)
- Has many: Product Process Overrides
- Links to: Challenges (many-to-many)
- Links to: Technologies (many-to-many)

---

#### **Indications**
Clinical indications for products.

**Schema:**
```python
indication_id (PK)
product_id (FK → products.product_id)
indication_name
therapeutic_area
development_phase
expected_launch_year
```

**JSON Import Example:**
```json
{
  "product_code": "BI 1015550",
  "indication_name": "Progressive Pulmonary Fibrosis (PPF)",
  "therapeutic_area": "Respiratory",
  "development_phase": "Phase 3",
  "expected_launch_year": 2026
}
```

---

### Requirements System (Dual-Path Pattern)

#### **Modality Requirements** (Pattern Level)
Standard capabilities required by a modality.

**Schema:**
```python
modality_id (PK, FK)
required_capability_id (PK, FK)
requirement_level ('essential', 'preferred', 'optional')
is_critical (boolean)
timeline_context
```

**JSON Import Example:**
```json
{
  "modality_name": "Monoclonal Antibody",
  "required_capability_name": "Cell Culture (Mammalian)",
  "requirement_level": "essential",
  "is_critical": true,
  "timeline_context": "Required from Phase 1 through commercial"
}
```

---

#### **Product Requirements** (Specific Level)
Product-specific capability needs (overrides or additions to modality).

**Schema:**
```python
product_id (PK, FK)
required_capability_id (PK, FK)
requirement_level
is_critical
timeline_needed (date)
notes
```

**JSON Import Example:**
```json
{
  "product_code": "BI 456906",
  "required_capability_name": "Device Assembly & Integration",
  "requirement_level": "essential",
  "is_critical": true,
  "timeline_needed": "2026-06-01",
  "notes": "Specific to pen injector device for peptide delivery"
}
```

---

### Manufacturing Network

#### **Manufacturing Entities** (Base Table)
Polymorphic base for facilities and partners.

**Schema:**
```python
entity_id (PK)
entity_name
entity_type ('Internal' or 'External')
location
operational_status
created_at
```

**Used as base for:**
- Internal Facilities (extends with facility_code, cost_center, etc.)
- External Partners (extends with company_name, relationship_type, etc.)

---

#### **Internal Facilities**
Company-owned manufacturing sites.

**Schema:**
```python
entity_id (PK, FK → manufacturing_entities)
facility_code
cost_center
facility_type
compatible_product_types (JSONB)
internal_capacity (JSONB)
```

**JSON Import Example:**
```json
{
  "facility_code": "ING",
  "entity_name": "Ingelheim Site",
  "location": "Germany",
  "facility_type": "Integrated Biologics & Small Molecule",
  "operational_status": "Active",
  "compatible_product_types": ["NCE", "NBE"],
  "internal_capacity": {
    "API_synthesis_kg_per_year": 5000,
    "tablet_production_million_units": 200
  }
}
```

---

#### **External Partners**
Contract manufacturing organizations (CMOs).

**Schema:**
```python
entity_id (PK, FK → manufacturing_entities)
company_name
relationship_type
contract_terms
exclusivity_level
capacity_allocation
specialization
```

**JSON Import Example:**
```json
{
  "company_name": "Vetter Pharma",
  "entity_name": "Vetter Pharma",
  "location": "Ravensburg, Germany",
  "relationship_type": "CMO - Fill & Finish",
  "operational_status": "Active",
  "contract_terms": "Master Service Agreement through 2027",
  "exclusivity_level": "Preferred Partner",
  "specialization": "Aseptic fill-finish for biologics and pre-filled syringes"
}
```

---

#### **Entity Capabilities**
What each facility/partner can do.

**Schema:**
```python
entity_id (PK, FK)
capability_id (PK, FK)
capability_level ('basic', 'intermediate', 'advanced', 'expert')
implementation_date
upgrade_planned (boolean)
notes
```

**JSON Import Example:**
```json
{
  "entity_name": "Biberach",
  "capability_name": "Cell Culture (Mammalian)",
  "capability_level": "expert",
  "implementation_date": "2015-03-01",
  "upgrade_planned": false,
  "notes": "20,000L single-use bioreactor capacity"
}
```

---

#### **Product Supply Chain**
Maps products to manufacturing entities.

**Schema:**
```python
id (PK)
product_id (FK)
entity_id (FK)
manufacturing_stage
supply_model ('Internal', 'External', 'Hybrid')
internal_site_name
```

**JSON Import Example:**
```json
{
  "product_code": "BI 764532",
  "entity_name": "Vetter",
  "manufacturing_stage": "Fill & Finish",
  "supply_model": "External"
}
```

---

### Process Templates

#### **Process Templates**
Standard process flow for each modality.

**Schema:**
```python
template_id (PK)
modality_id (FK)
template_name
description
created_at
```

**JSON Import Example:**
```json
{
  "template_name": "Standard Monoclonal Antibody Process",
  "modality_name": "Monoclonal Antibody",
  "description": "Typical CHO cell-based mAb production process",
  "stages": [
    {
      "stage_name": "Upstream Processing",
      "stage_order": 1,
      "is_required": true,
      "base_capabilities": ["Cell Culture (Mammalian)", "Bioreactor Operation"]
    },
    {
      "stage_name": "Downstream Processing",
      "stage_order": 2,
      "is_required": true,
      "base_capabilities": ["Protein Purification", "Chromatography"]
    }
  ]
}
```

---

## Key Concepts

### 1. Hierarchical Process Stages

Process stages can nest to any depth:

```
Chemical Synthesis (Level 1: Phase)
  └─ Raw Material Management (Level 2: Stage)
      ├─ Sourcing & Qualification (Level 3: Operation)
      │   ├─ Vendor Audits (Level 4: Activity)
      │   └─ Material Testing (Level 4: Activity)
      └─ Supply Chain Management (Level 3: Operation)
```

**Benefits:**
- Query at any level of granularity
- Challenges and technologies link at appropriate level
- Support both high-level and detailed analysis

**Usage:**
```python
# Get top-level phases
phases = ProcessStage.get_top_level_phases()

# Get full hierarchical path
operation.get_full_path()
# Returns: "Chemical Synthesis > Raw Material Management > Sourcing & Qualification"
```

---

### 2. Dual-Path Requirements Pattern

Requirements exist at both pattern and specific levels:

```
PATTERN LEVEL (Inherited):
Modality "mAb" → requires "Cell Culture"
  ↓ (all mAb products inherit this)
Product "mAb-123" → gets Cell Culture requirement

SPECIFIC LEVEL (Override/Addition):
Product "mAb-123" → also requires "Novel Purification"
  ↑ (product-specific need not in modality)
```

**Benefits:**
- Define once at modality level (DRY principle)
- Override for special cases at product level
- Complete picture = inherited + specific

---

### 3. Challenge Anchoring

Challenges connect at multiple levels:

```
Challenge: "BSL-2+ Containment"
  ├─ Primary Stage: "Upstream Processing" (context)
  ├─ Products: [specific products facing this] (facts)
  └─ Related Capabilities: ["BSL-2+ Facilities"] (solutions)
```

**Benefits:**
- Know WHERE challenges occur (stage)
- Know WHICH products face them (direct link)
- Know HOW to address them (capabilities)

---

## Data Population Strategy

### Phase 1: Foundation (Start Here)
1. **Modalities** (5-10 entries) - Already complete
2. **Process Stages** (10-15 Level 1 phases)
3. **Manufacturing Capabilities** (20-30 core capabilities)

### Phase 2: Context
4. **Manufacturing Technologies** (15-20 entries)
5. **Manufacturing Challenges** (extract from modalities.json)

### Phase 3: Products & Patterns
6. **Process Templates** (one per modality)
7. **Products** (import from failsafe.json)
8. **Modality Requirements** (pattern-level)

### Phase 4: Manufacturing Network
9. **Manufacturing Entities** (facilities + partners)
10. **Entity Capabilities** (what each can do)
11. **Product Supply Chain** (product-to-entity mapping)

### Phase 5: Details
12. **Product Requirements** (specific overrides)
13. **Indications** (clinical details)

---

## Import Workflow

### Step 1: Prepare JSON File
Create file in `content/` directory (e.g., `process_stages.json`)

### Step 2: Navigate to Data Management
Go to **Data Management** page in application

### Step 3: Select Entity Type & Upload
- Choose entity type from dropdown
- Upload JSON file
- Click "Analyze File"

### Step 4: Review Preview
- See proposed adds/updates/skips
- Use bulk actions or individual controls
- Validate relationships resolve correctly

### Step 5: Finalize Import
- Click "Finalize Import"
- System commits changes to database
- Check logs for any errors

---

## Common Patterns

### Product with Full Context
```json
{
  "product_code": "EXAMPLE-001",
  "product_name": "Example Product",
  "modality_name": "Monoclonal Antibody",
  "therapeutic_area": "Oncology",
  "current_phase": "Phase 2",
  "expected_launch_year": 2028
}
```

Then separately link challenges:
```json
{
  "challenge_name": "High Titer Production",
  "product_codes": ["EXAMPLE-001"]
}
```

### Hierarchical Stage Definition
```json
[
  {"stage_name": "Upstream", "hierarchy_level": 1, "stage_order": 1},
  {"stage_name": "Cell Culture", "hierarchy_level": 2, "parent_stage_name": "Upstream", "stage_order": 1},
  {"stage_name": "Seed Train", "hierarchy_level": 3, "parent_stage_name": "Cell Culture", "stage_order": 1}
]
```

### Capability Requirement Chain
```json
// 1. Define capability
{"capability_name": "Continuous Manufacturing", "complexity_weight": 9}

// 2. Link to modality
{"modality_name": "Small Molecule", "required_capability_name": "Continuous Manufacturing", "is_critical": true}

// 3. Optionally override at product level
{"product_code": "SM-001", "required_capability_name": "Advanced Continuous (TSG)", "is_critical": true}
```

---

## Validation Rules

### Unique Constraints
- `product_code` must be unique
- `modality_name` must be unique
- `stage_name` must be unique (even across hierarchy levels)
- `capability_name` must be unique
- `challenge_name` must be unique

### Required Fields
- Products must have: `product_code`, `product_name`
- Stages must have: `stage_name`, `hierarchy_level`
- Capabilities must have: `capability_name`

### Referential Integrity
- All `*_name` fields in JSON must resolve to existing entities
- System will error if referenced entity doesn't exist
- Create parent entities before children (modality before products)

---

## Querying Examples

### Find all challenges for a product
```python
product = Product.query.filter_by(product_code="BI 1015550").first()
challenges = product.challenges  # Direct link
```

### Get product complexity score
```python
from sqlalchemy import func
complexity = db.session.query(
    func.sum(ManufacturingCapability.complexity_weight)
).join(ProductRequirement).filter(
    ProductRequirement.product_id == product.id
).scalar()
```

### Navigate stage hierarchy
```python
stage = ProcessStage.query.filter_by(stage_name="Sourcing & Qualification").first()
path = stage.get_full_path()  # "Chemical Synthesis > Raw Material > Sourcing & Qualification"
children = stage.children  # All sub-operations
parent = stage.parent  # Parent stage
```

---

This schema provides a comprehensive foundation for modeling pharmaceutical manufacturing complexity while maintaining flexibility for future enhancements.