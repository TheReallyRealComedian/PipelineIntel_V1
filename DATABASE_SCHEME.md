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
  ├─ Requires: Cell Culture (Mammalian)
  ├─ Requires: Protein Purification
  ├─ Requires: Fill & Finish (Aseptic)
  └─ Standard Challenges: High Titer Production, Aggregation Control
  
All 150+ mAb products inherit these requirements automatically.
```

---

### 2. Process Templates: Manufacturing Blueprints

**What they are**: Standard process flows for a specific manufacturing approach within a modality.

**Why they exist**: Not all products in a modality are made the same way. Modern manufacturing offers choices (e.g., batch vs continuous), and these choices affect what capabilities you need.

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

**Relationship to Stages**: Technologies belong to ONE primary stage where they're used.

**Schema**:
```python
technology_id (PK)
technology_name (unique)
stage_id (FK → process_stages.stage_id)
innovation_potential (text)
complexity_rating (1-10)
```

**Concrete Example**:
```json
{
  "technology_name": "Twin Screw Granulation (TSG)",
  "stage_name": "Granulation",
  "innovation_potential": "High - enables continuous manufacturing",
  "complexity_rating": 7,
  "description": "Continuous wet granulation using twin screw extruder..."
}
```

**Links to Products**: Many-to-many (products can use multiple technologies).

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
- Challenges are specific to HOW you do something, not WHERE
- Example: "Sterility Assurance" is a challenge of "Aseptic Fill-Finish Technology", not just the "Fill & Finish" stage in general

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
- `modality_id` defines what the product IS
- `process_template_id` defines HOW it's made
- The template MUST belong to the modality (enforced by validation)

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
1. Modality requirements (all small molecules need X)
2. Template stage capabilities (continuous process needs Y)
3. Plus its own specific requirements (Nerandomilast also needs Z)

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
standard_challenges (JSONB) # Legacy field
created_at
```

**Relationships**:
- Has many: Products (`products.modality_id`)
- Has many: Process Templates (`process_templates.modality_id`)
- Has many: Modality Requirements (to Capabilities)

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
- Referenced by: Template Stages (via base_capabilities JSONB)
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

**The base_capabilities field**: Stores capability names needed for this stage WHEN using this template.

**Relationships**:
- Belongs to: Process Template
- Belongs to: Process Stage

**Why it's a composite key**: One template can use the same stage multiple times? No. But it ensures uniqueness of the (template, stage) pair.

---

### Manufacturing Context Entities

#### Manufacturing Technologies
```python
# Schema
technology_id (PK)
technology_name (unique) # "Twin Screw Granulation"
stage_id (FK → process_stages.stage_id)
innovation_potential (text)
complexity_rating (1-10)
```

**Relationships**:
- Belongs to: Process Stage (primary stage of use)
- Has many: Challenges (`challenges.technology_id`)
- Links to: Products (many-to-many via product_to_technology)

**JSON Import Example**:
```json
{
  "technology_name": "Perfusion Bioreactor System",
  "stage_name": "Cell Culture",
  "innovation_potential": "High - enables intensified bioprocessing",
  "complexity_rating": 8,
  "description": "Continuous cell culture system with cell retention..."
}
```

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
- Links to: Products (many-to-many with relationship_type)
- Implicit: Belongs to Stage (via technology)

**Product Linking Logic**:
- `relationship_type = 'explicit'`: Product faces this challenge
- `relationship_type = 'excluded'`: Product explicitly DOESN'T face this (overrides inheritance)

**JSON Import Example**:
```json
{
  "challenge_name": "Cell Line Stability at High Density",
  "challenge_category": "Production",
  "technology_name": "Perfusion Bioreactor System",
  "severity_level": "major",
  "related_capabilities": [
    "Advanced Cell Line Engineering",
    "Real-Time Cell Viability Monitoring",
    "Perfusion Process Control"
  ],
  "product_codes": ["BI 456789"] # Products that face this
}
```

---

### Product Entities

#### Products
```python
# Schema (Key Fields)
product_id (PK)
product_code (unique)
product_name
modality_id (FK → modalities.modality_id)
process_template_id (FK → process_templates.template_id)
product_type # "NCE", "NBE", etc.
therapeutic_area
current_phase
expected_launch_year
# ... many more fields
```

**Critical Foreign Keys**:
- `modality_id`: Links to category (WHAT it is)
- `process_template_id`: Links to process (HOW it's made)

**Validation Rule**: If both are set, template MUST belong to modality.

**Relationships**:
- Belongs to: Modality
- Belongs to: Process Template (nullable)
- Has many: Indications
- Has many: Product Requirements (specific capabilities)
- Has many: Product Process Overrides (process deviations)
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
  "current_phase": "Phase 2",
  "expected_launch_year": 2028
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

**JSON Import Example**:
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

**JSON Import Example**:
```json
{
  "product_code": "BI 456789",
  "required_capability_name": "Novel ADC Conjugation",
  "requirement_level": "essential",
  "is_critical": true,
  "timeline_needed": "2026-06-01",
  "notes": "Unique to this antibody-drug conjugate"
}
```

---

## Data Flow Examples

### Example 1: Complete Capability Requirements for a Product

**Product**: BI 456789 (Perfusion mAb for Oncology)

```python
# Query the product's complete requirements
product = Product.query.filter_by(product_code="BI 456789").first()
requirements = product.get_all_capability_requirements()

# Result Structure:
{
  'modality_inherited': [
    # From Modality: "Monoclonal Antibody"
    {'capability': 'Cell Culture (Mammalian)', 'source': 'Modality: Monoclonal Antibody'},
    {'capability': 'Protein Purification', 'source': 'Modality: Monoclonal Antibody'},
    {'capability': 'Fill & Finish (Aseptic)', 'source': 'Modality: Monoclonal Antibody'}
  ],
  
  'template_inherited': [
    # From Template: "Perfusion mAb Process" → Template Stages
    {'capability': 'Perfusion Bioreactor Operation', 'stage': 'Cell Culture'},
    {'capability': 'Continuous Harvest Systems', 'stage': 'Cell Culture'},
    {'capability': 'Real-Time Analytics', 'stage': 'Cell Culture'},
    {'capability': 'Protein A Chromatography', 'stage': 'Purification'}
  ],
  
  'product_specific': [
    # Product-specific additions
    {'capability': 'Novel ADC Conjugation', 'notes': 'Unique to this ADC'}
  ]
}
```

**Total Requirements**: Union of all three tiers.

---

### Example 2: Challenge Inheritance

**Scenario**: Product uses "Perfusion Bioreactor System" technology.

```python
# Technology has associated challenges
technology = ManufacturingTechnology.query.filter_by(
    technology_name="Perfusion Bioreactor System"
).first()

# Challenges linked to this technology:
technology.challenges
# Returns:
# - "Cell Line Stability at High Density"
# - "Perfusion Process Control Complexity"
# - "Equipment Fouling Risk"

# Product inherits these challenges automatically
product.get_inherited_challenges()
# Returns all challenges from linked technologies

# Product can exclude inherited challenges
product.add_challenge_exclusion(
    challenge_id=15,  # "Equipment Fouling Risk"
    notes="Using novel anti-fouling membrane technology"
)

# Product can add explicit challenges
product.add_challenge_inclusion(
    challenge_id=42,  # "Regulatory Uncertainty - Novel Process"
    notes="First-in-class perfusion approval pathway"
)

# Final effective challenges
product.get_effective_challenges()
# Returns: Inherited - Excluded + Explicit
```

---

### Example 3: Hierarchical Stage Navigation

```python
# Find all operations under Upstream Processing
upstream = ProcessStage.query.filter_by(
    stage_name="Upstream Processing"
).first()

# Get all child stages
upstream.children
# Returns: Cell Culture, Media Preparation, Inoculation, etc.

# Get full path for a detailed operation
operation = ProcessStage.query.filter_by(
    stage_name="Vial Thaw"
).first()

operation.get_full_path()
# Returns: "Upstream Processing > Cell Culture > Seed Train > Vial Thaw"

# Query products by stage at any level
products_using_perfusion = Product.query.join(
    product_to_technology_association
).join(ManufacturingTechnology).join(ProcessStage).filter(
    ProcessStage.stage_name == "Cell Culture"
).all()
```

---

## Common Patterns

### Pattern 1: Adding a New Modality

1. Create the modality
2. Define modality requirements (common capabilities)
3. Create at least one process template
4. Define template stages with base_capabilities
5. Products can now use this modality + template

```json
// Step 1: Modality
{
  "modality_name": "Oligonucleotide",
  "modality_category": "Nucleic Acid Therapeutics"
}

// Step 2: Modality Requirements
{
  "modality_name": "Oligonucleotide",
  "required_capability_name": "Solid-Phase Synthesis",
  "requirement_level": "essential"
}

// Step 3: Template
{
  "template_name": "Standard Oligo Process",
  "modality_name": "Oligonucleotide",
  "stages": [...]
}

// Step 4: Products
{
  "product_code": "OLIGO-001",
  "modality_name": "Oligonucleotide",
  "process_template_name": "Standard Oligo Process"
}
```

---

### Pattern 2: Process Variations

When a modality has multiple process approaches:

```json
// Same modality, different templates
{
  "modality_name": "Small Molecule",
  "templates": [
    {
      "template_name": "Batch Small Molecule",
      "stages": [
        {
          "stage_name": "API Synthesis",
          "base_capabilities": ["Batch Reactor Operation"]
        }
      ]
    },
    {
      "template_name": "Continuous Small Molecule",
      "stages": [
        {
          "stage_name": "API Synthesis",
          "base_capabilities": ["Continuous Flow Reactor", "Twin Screw Granulation"]
        }
      ]
    }
  ]
}
```

Products choose which template based on their manufacturing approach.

---

### Pattern 3: Challenge Management

```json
// Define challenge (linked to technology, not stage directly)
{
  "challenge_name": "High Containment Requirements",
  "technology_name": "Live Viral Vector Production",
  "severity_level": "critical",
  "related_capabilities": ["BSL-2+ Facilities", "Viral Safety Protocols"]
}

// Products inherit from technologies
Product "GENE-001" uses "Live Viral Vector Production"
  → Automatically inherits "High Containment Requirements"

// Product can exclude if not applicable
{
  "product_code": "GENE-001",
  "excluded_challenge_name": "High Containment Requirements",
  "notes": "Using inactivated vector"
}
```

---

## Import Guidelines

### Import Order (Critical!)

Dependencies must be imported in this order:

1. **Foundation**: Modalities, Process Stages, Manufacturing Capabilities
2. **Context**: Manufacturing Technologies, Manufacturing Challenges
3. **Templates**: Process Templates (with stages)
4. **Products**: Products (references modalities + templates)
5. **Requirements**: Modality Requirements, Product Requirements
6. **Mappings**: Product-Technology links, Product-Challenge links

### Name-Based Foreign Key Resolution

The import system resolves foreign keys by name:

```json
// Instead of this (error-prone):
{"modality_id": 5}

// Use this (human-readable):
{"modality_name": "Monoclonal Antibody"}

// System automatically looks up:
modality_id = Modality.query.filter_by(modality_name="Monoclonal Antibody").first().modality_id
```

### Nested vs Separate Imports

**Nested Import** (Template with Stages):
```json
{
  "template_name": "Fed-Batch mAb",
  "modality_name": "Monoclonal Antibody",
  "stages": [
    {"stage_name": "Upstream", "stage_order": 1, "base_capabilities": [...]},
    {"stage_name": "Downstream", "stage_order": 2, "base_capabilities": [...]}
  ]
}
```

**Separate Imports** (Product and Challenges):
```json
// First: Product
{"product_code": "BI 123", "product_name": "..."}

// Then: Link to Challenges
{
  "challenge_name": "High Titer Production",
  "product_codes": ["BI 123", "BI 456"]
}
```

---

## Troubleshooting & FAQs

### Q: Why can't I add a check constraint for template-modality matching?

**A**: PostgreSQL doesn't support subqueries in CHECK constraints. Validation is handled at the application level via the `@validates` decorator in the Product model.

**Solution**: The model automatically validates on insert/update. If you need database-level enforcement, use a trigger (see optional trigger migration).

---

### Q: Can a product have no template?

**A**: Yes. `process_template_id` is nullable. Some products may have completely bespoke processes that don't fit standard templates.

---

### Q: Why are challenges linked to technologies instead of stages?

**A**: Because challenges are specific to HOW you do something, not just WHERE. 

**Example**: "Upstream Processing" stage might use:
- Fed-Batch Technology → Challenge: "Long cycle times"
- Perfusion Technology → Challenge: "Membrane fouling"

Same stage, different challenges based on technology choice.

---

### Q: What's the difference between modality_requirements and template_stages.base_capabilities?

**A**: 
- **Modality Requirements**: Capabilities needed for ALL products in that category (stored in database table)
- **Template Base Capabilities**: Capabilities needed for a specific PROCESS APPROACH (stored in JSONB field)

**Example**:
- Modality Requirement: "All mAbs need cell culture" (applies to 100+ products)
- Template Capability: "Fed-batch mAbs need fed-batch bioreactors" (applies to ~60 products)

---

### Q: Can a template belong to multiple modalities?

**A**: No. Each template belongs to exactly one modality. If two modalities share the same process, create separate templates (can duplicate the stages).

---

### Q: How do I query all capabilities for a product?

**A**: Use the built-in method:

```python
product = Product.query.get(product_id)
all_requirements = product.get_all_capability_requirements()
# Returns dict with modality_inherited, template_inherited, product_specific
```

---

### Q: Can I modify a template after products are using it?

**A**: Yes, but be careful. Changes to `template_stages.base_capabilities` will affect ALL products using that template. If you need to change requirements for one product, use `product_requirements` instead.

---

## Appendix: Database Diagram Legend

When viewing the schema diagram:

- **Solid lines**: Foreign key relationships
- **Dotted lines**: Logical/derived relationships
- **Bold tables**: Central hub entities (Products, Modalities)
- **Grouped boxes**: Related entity clusters

**Key Relationships**:
```
Products (central hub)
  ├─── modality_id → Modalities
  ├─── process_template_id → Process Templates
  ├─── many-to-many → Technologies
  ├─── many-to-many → Challenges
  └─── one-to-many → Product Requirements

Process Templates
  ├─── modality_id → Modalities
  └─── many-to-many → Process Stages (via Template Stages)

Manufacturing Technologies
  ├─── stage_id → Process Stages
  └─── one-to-many → Challenges
```

---

## Version History

- **v2.0** (2025-10-05): Added process_template_id to products, clarified three-tier inheritance, removed primary_stage_id redundancy
- **v1.0** (2025-07-15): Initial schema design

---

**Questions?** Check the code comments in `backend/models.py` or the migration files in `migrations/versions/` for implementation details.