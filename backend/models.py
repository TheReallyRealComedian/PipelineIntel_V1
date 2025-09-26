# backend/models.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Table, Boolean, Date
from sqlalchemy.orm import relationship, column_property
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.inspection import inspect
from passlib.hash import pbkdf2_sha256
from flask_login import UserMixin
from .db import db
from sqlalchemy.orm.properties import RelationshipProperty

# --- Association Tables ---
product_to_challenge_association = Table(
    'product_to_challenge', db.metadata,
    Column('product_id', Integer, ForeignKey('products.product_id'), primary_key=True),
    Column('challenge_id', Integer, ForeignKey('manufacturing_challenges.challenge_id'), primary_key=True),
    Column('relationship_type', String(20), default='explicit'),  # 'explicit', 'excluded'
    Column('notes', Text, nullable=True)
)

product_to_technology_association = Table('product_to_technology', db.metadata,
    Column('product_id', Integer, ForeignKey('products.product_id'), primary_key=True),
    Column('technology_id', Integer, ForeignKey('manufacturing_technologies.technology_id'), primary_key=True)
)

# --- Core Entity Tables ---

class Product(db.Model):
    __tablename__ = 'products'
    product_id = Column(Integer, primary_key=True)
    product_code = Column(String(100), unique=True, nullable=False, index=True)
    product_name = Column(String(255), nullable=True)

    # Core Product Info
    product_type = Column(String(100), nullable=True)
    short_description = Column(Text, nullable=True) # CHANGED from String(255)
    description = Column(Text, nullable=True)
    base_technology = Column(String(255), nullable=True)
    mechanism_of_action = Column(Text, nullable=True)
    dosage_form = Column(String(255), nullable=True)
    therapeutic_area = Column(String(255), nullable=True, index=True)

    # Development & Regulatory Status
    current_phase = Column(String(100), nullable=True, index=True)
    project_status = Column(String(100), nullable=True, index=True)
    lead_indication = Column(String(255), nullable=True)
    expected_launch_year = Column(Integer, nullable=True)
    # Use JSONB for arrays and nested objects
    lifecycle_indications = Column(JSONB, nullable=True)
    regulatory_designations = Column(JSONB, nullable=True)

    # Manufacturing & Supply Chain
    manufacturing_strategy = Column(String(100), nullable=True)
    manufacturing_sites = Column(JSONB, nullable=True)
    volume_forecast = Column(JSONB, nullable=True)

    # New Field from Phase 1
    modality_id = Column(Integer, ForeignKey('modalities.modality_id'))

    # ==================== NEW FORMULATION FIELDS ====================
    primary_packaging = Column(String(100), nullable=True)
    route_of_administration = Column(String(100), nullable=True)
    biel_category = Column(String(20), nullable=True)
    granulation_technology = Column(String(255), nullable=True)

    # ==================== NEW REGULATORY FIELDS ====================
    submission_status = Column(String(100), nullable=True)
    submission_date = Column(Date, nullable=True)
    approval_date = Column(Date, nullable=True)
    launch_geography = Column(String(255), nullable=True)
    regulatory_details = Column(JSONB, nullable=True)

    # ==================== NEW OPERATIONAL FIELDS ====================
    ppq_status = Column(String(100), nullable=True)
    ppq_completion_date = Column(Date, nullable=True)
    ppq_details = Column(JSONB, nullable=True)
    timeline_variance_days = Column(Integer, nullable=True)
    timeline_variance_baseline = Column(String(50), nullable=True)
    critical_path_item = Column(String(255), nullable=True)
    ds_volume_category = Column(String(100), nullable=True)
    dp_volume_category = Column(String(100), nullable=True)

    # ==================== NEW SUPPLY CHAIN FIELDS ====================
    ds_suppliers = Column(JSONB, nullable=True)
    dp_suppliers = Column(JSONB, nullable=True)
    device_partners = Column(JSONB, nullable=True)

    # ==================== NEW RISK FIELDS ====================
    operational_risks = Column(JSONB, nullable=True)
    timeline_risks = Column(JSONB, nullable=True)
    supply_chain_risks = Column(JSONB, nullable=True)

    # ==================== NEW CLINICAL FIELDS ====================
    clinical_trials = Column(JSONB, nullable=True)
    patient_population = Column(Text, nullable=True)
    development_program_name = Column(String(255), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships
    indications = relationship("Indication", back_populates="product", cascade="all, delete-orphan")
    supply_chain = relationship("ProductSupplyChain", back_populates="product", cascade="all, delete-orphan")
    challenges = relationship("ManufacturingChallenge", secondary=product_to_challenge_association, back_populates="products")
    technologies = relationship("ManufacturingTechnology", secondary=product_to_technology_association, back_populates="products")
    process_overrides = relationship("ProductProcessOverride", back_populates="product", cascade="all, delete-orphan")
    requirements = relationship("ProductRequirement", back_populates="product")
    # This line is correct. It points to 'products' on the Modality model.
    modality = relationship("Modality", back_populates="products")

    @classmethod
    def get_all_fields(cls):
        """
        Returns a list of all column/property names for the model,
        correctly excluding relationship objects.
        """
        inspector = inspect(cls)
        # This logic ensures only simple columns are returned, not entire related objects.
        return [
            c.key for c in inspector.attrs 
            if not isinstance(c, RelationshipProperty) and not c.key.startswith('_')
        ]
    

    def get_inherited_challenges(self):
        """Get challenges inherited from modality's process template."""
        if not self.modality_id:
            return []
        
        # Get the process template for this modality
        template = ProcessTemplate.query.filter_by(modality_id=self.modality_id).first()
        if not template:
            return []
        
        # Get all challenges from template stages
        inherited_challenges = db.session.query(ManufacturingChallenge).join(
            ProcessStage, ManufacturingChallenge.primary_stage_id == ProcessStage.stage_id
        ).join(
            TemplateStage, ProcessStage.stage_id == TemplateStage.stage_id
        ).filter(
            TemplateStage.template_id == template.template_id
        ).distinct().all()
        
        return inherited_challenges

    def get_explicit_challenge_relationships(self):
        """Get user-defined challenge relationships (exclusions/inclusions)."""
        from sqlalchemy import text
        
        result = db.session.execute(
            text("""
            SELECT challenge_id, relationship_type, notes 
            FROM product_to_challenge 
            WHERE product_id = :product_id
            """),
            {'product_id': self.product_id}
        )
        
        return [
            {
                'challenge_id': row[0],
                'relationship_type': row[1], 
                'notes': row[2]
            } for row in result
        ]

    def get_effective_challenges(self):
        """Get final list of challenges (inherited - excluded + explicit)."""
        inherited = self.get_inherited_challenges()
        explicit_relationships = self.get_explicit_challenge_relationships()
        
        # Create lookup for explicit relationships
        explicit_lookup = {rel['challenge_id']: rel for rel in explicit_relationships}
        
        effective_challenges = []
        
        # Start with inherited challenges, exclude any marked as 'excluded'
        for challenge in inherited:
            if challenge.challenge_id in explicit_lookup:
                rel = explicit_lookup[challenge.challenge_id]
                if rel['relationship_type'] == 'excluded':
                    continue  # Skip excluded challenges
            
            effective_challenges.append({
                'challenge': challenge,
                'source': 'inherited',
                'notes': explicit_lookup.get(challenge.challenge_id, {}).get('notes')
            })
        
        # Add explicitly included challenges that aren't already inherited
        inherited_ids = {c.challenge_id for c in inherited}
        
        for rel in explicit_relationships:
            if rel['relationship_type'] == 'explicit' and rel['challenge_id'] not in inherited_ids:
                challenge = ManufacturingChallenge.query.get(rel['challenge_id'])
                if challenge:
                    effective_challenges.append({
                        'challenge': challenge,
                        'source': 'explicit',
                        'notes': rel['notes']
                    })
        
        return effective_challenges

    def add_challenge_exclusion(self, challenge_id, notes=None):
        """Exclude an inherited challenge."""
        # Check if this challenge is actually inherited
        inherited_ids = {c.challenge_id for c in self.get_inherited_challenges()}
        if challenge_id not in inherited_ids:
            raise ValueError("Cannot exclude a challenge that is not inherited")
        
        # Remove any existing relationship
        from sqlalchemy import text
        db.session.execute(
            text("DELETE FROM product_to_challenge WHERE product_id = :pid AND challenge_id = :cid"),
            {'pid': self.product_id, 'cid': challenge_id}
        )
        
        # Add exclusion
        db.session.execute(
            text("""
            INSERT INTO product_to_challenge (product_id, challenge_id, relationship_type, notes) 
            VALUES (:pid, :cid, 'excluded', :notes)
            """),
            {'pid': self.product_id, 'cid': challenge_id, 'notes': notes}
        )
        
        db.session.commit()

    def add_challenge_inclusion(self, challenge_id, notes=None):
        """Add a product-specific challenge."""
        # Check if challenge exists
        if not ManufacturingChallenge.query.get(challenge_id):
            raise ValueError("Challenge does not exist")
        
        # Remove any existing relationship
        from sqlalchemy import text
        db.session.execute(
            text("DELETE FROM product_to_challenge WHERE product_id = :pid AND challenge_id = :cid"),
            {'pid': self.product_id, 'cid': challenge_id}
        )
        
        # Add inclusion
        db.session.execute(
            text("""
            INSERT INTO product_to_challenge (product_id, challenge_id, relationship_type, notes) 
            VALUES (:pid, :cid, 'explicit', :notes)
            """),
            {'pid': self.product_id, 'cid': challenge_id, 'notes': notes}
        )
        
        db.session.commit()

    def remove_challenge_relationship(self, challenge_id):
        """Remove any explicit relationship (exclusion or inclusion)."""
        from sqlalchemy import text
        db.session.execute(
            text("DELETE FROM product_to_challenge WHERE product_id = :pid AND challenge_id = :cid"),
            {'pid': self.product_id, 'cid': challenge_id}
        )
        db.session.commit()

class Indication(db.Model):
    __tablename__ = 'indications'
    indication_id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.product_id'), nullable=False)
    indication_name = Column(String(255), nullable=False)
    therapeutic_area = Column(String(255), nullable=True)
    development_phase = Column(String(100), nullable=True)
    expected_launch_year = Column(Integer, nullable=True)
    product = relationship("Product", back_populates="indications")

    @classmethod
    def get_all_fields(cls):
        """Returns a list of all column names for the model."""
        return [c.key for c in inspect(cls).attrs if c.key not in ['product']]

class ManufacturingChallenge(db.Model):
    __tablename__ = 'manufacturing_challenges'
    challenge_id = Column(Integer, primary_key=True)
    challenge_category = Column(String(255), nullable=False, index=True)
    challenge_name = Column(String(255), unique=True, nullable=False)
    short_description = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    related_capabilities = Column(JSONB)
    
    # NEW: Link to primary process stage where this challenge occurs
    primary_stage_id = Column(Integer, ForeignKey('process_stages.stage_id'))
    severity_level = Column(String(50))  # 'minor', 'moderate', 'major', 'critical'
    
    # Relationships
    products = relationship("Product", secondary=product_to_challenge_association, back_populates="challenges")
    primary_stage = relationship("ProcessStage", back_populates="challenges")  # NEW

    @classmethod
    def get_all_fields(cls):
        """Returns a list of all column names for the model."""
        return [c.key for c in inspect(cls).attrs if c.key not in ['products', 'primary_stage']]

class ManufacturingTechnology(db.Model):
    __tablename__ = 'manufacturing_technologies'
    technology_id = Column(Integer, primary_key=True)
    technology_name = Column(String(255), unique=True, nullable=False)
    short_description = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    stage_id = Column(Integer, ForeignKey('process_stages.stage_id')) # New field from Phase 3
    innovation_potential = Column(Text) # New field from Phase 3
    complexity_rating = Column(Integer) # New field from Phase 3
    stage = relationship("ProcessStage", back_populates="technologies")
    products = relationship("Product", secondary=product_to_technology_association, back_populates="technologies")

    @classmethod
    def get_all_fields(cls):
        """Returns a list of all column names for the model."""
        return [c.key for c in inspect(cls).attrs if c.key not in ['stage', 'products']]

class ProductSupplyChain(db.Model):
    __tablename__ = 'product_supply_chain'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.product_id'), nullable=False)
    manufacturing_stage = Column(String(255), nullable=False)
    supply_model = Column(String(100), nullable=True)
    entity_id = Column(Integer, ForeignKey('manufacturing_entities.entity_id'), nullable=True)
    internal_site_name = Column(String(255), nullable=True)
    product = relationship("Product", back_populates="supply_chain")
    manufacturing_entity = relationship("ManufacturingEntity", back_populates="supply_chain_links")

# --- New Models from Phase 1 ---

class Modality(db.Model):
    __tablename__ = 'modalities'
    modality_id = Column(Integer, primary_key=True)
    modality_name = Column(String(255), unique=True, nullable=False)
    modality_category = Column(String(255))
    label = Column(String(255), nullable=True)
    short_description = Column(Text, nullable=True) # CHANGED from String(255)
    description = Column(Text)
    standard_challenges = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    # THIS IS THE CORRECTED LINE. It points back to 'modality' on the Product model.
    products = relationship("Product", back_populates="modality")
    process_templates = relationship("ProcessTemplate", back_populates="modality")
    requirements = relationship("ModalityRequirement", back_populates="modality")

    @classmethod
    def get_all_fields(cls):
        """Returns a list of all column names for the model."""
        return [c.key for c in inspect(cls).attrs if c.key not in ['products', 'process_templates', 'requirements']]

class ManufacturingCapability(db.Model):
    __tablename__ = 'manufacturing_capabilities'
    capability_id = Column(Integer, primary_key=True)
    capability_name = Column(String(255), unique=True, nullable=False)
    capability_category = Column(String(255), index=True)
    approach_category = Column(String(255))
    description = Column(Text)
    complexity_weight = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships back to requirements
    modality_requirements = relationship("ModalityRequirement", back_populates="capability")
    product_requirements = relationship("ProductRequirement", back_populates="capability")
    entity_provisions = relationship("EntityCapability", back_populates="capability")

    @classmethod
    def get_all_fields(cls):
        """Returns a list of all column names for the model."""
        return [c.key for c in inspect(cls).attrs if not c.key.startswith('_') and c.key not in ['modality_requirements', 'product_requirements', 'entity_provisions']]

class ManufacturingEntity(db.Model):
    __tablename__ = 'manufacturing_entities'
    entity_id = Column(Integer, primary_key=True)
    entity_name = Column(String(255), nullable=False)
    entity_type = Column(String(50), nullable=False, index=True)
    location = Column(String(255))
    operational_status = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    supply_chain_links = relationship("ProductSupplyChain", back_populates="manufacturing_entity")
    internal_facility = relationship("InternalFacility", back_populates="entity", uselist=False, cascade="all, delete-orphan")
    # Note: `external_partner` relationship is defined in the ExternalPartner model below
    external_partner = relationship("ExternalPartner", back_populates="entity", uselist=False, cascade="all, delete-orphan")
    capabilities = relationship("EntityCapability", back_populates="entity", cascade="all, delete-orphan")

    @classmethod
    def get_all_fields(cls):
        """Returns a list of all column names for the model."""
        return [c.key for c in inspect(cls).attrs if not c.key.startswith('_') and c.key not in ['supply_chain_links', 'internal_facility', 'external_partner', 'capabilities']]


# --- New Models from Phase 2 ---

class ModalityRequirement(db.Model):
    __tablename__ = 'modality_requirements'
    modality_id = Column(Integer, ForeignKey('modalities.modality_id'), primary_key=True)
    required_capability_id = Column(Integer, ForeignKey('manufacturing_capabilities.capability_id'), primary_key=True)
    requirement_level = Column(String(100))
    is_critical = Column(Boolean, default=False)
    timeline_context = Column(Text)
    # Relationships
    modality = relationship("Modality", back_populates="requirements")
    capability = relationship("ManufacturingCapability", back_populates="modality_requirements")

class ProductRequirement(db.Model):
    __tablename__ = 'product_requirements'
    product_id = Column(Integer, ForeignKey('products.product_id'), primary_key=True)
    required_capability_id = Column(Integer, ForeignKey('manufacturing_capabilities.capability_id'), primary_key=True)
    requirement_level = Column(String(100))
    is_critical = Column(Boolean, default=False)
    timeline_needed = Column(Date)
    notes = Column(Text)
    # Relationships
    product = relationship("Product", back_populates="requirements")
    capability = relationship("ManufacturingCapability", back_populates="product_requirements")

class InternalFacility(db.Model):
    __tablename__ = 'internal_facilities'
    entity_id = Column(Integer, ForeignKey('manufacturing_entities.entity_id'), primary_key=True)
    facility_code = Column(String(100))
    cost_center = Column(String(100))
    facility_type = Column(String(100))
    compatible_product_types = Column(JSONB)
    internal_capacity = Column(JSONB)
    entity = relationship("ManufacturingEntity", back_populates="internal_facility")

class EntityCapability(db.Model):
    __tablename__ = 'entity_capabilities'
    entity_id = Column(Integer, ForeignKey('manufacturing_entities.entity_id'), primary_key=True)
    capability_id = Column(Integer, ForeignKey('manufacturing_capabilities.capability_id'), primary_key=True)
    capability_level = Column(String(100))
    implementation_date = Column(Date)
    upgrade_planned = Column(Boolean, default=False)
    notes = Column(Text)
    # Relationships
    entity = relationship("ManufacturingEntity", back_populates="capabilities")
    capability = relationship("ManufacturingCapability", back_populates="entity_provisions")

class ExternalPartner(db.Model):
    __tablename__ = 'external_partners'
    entity_id = Column(Integer, ForeignKey('manufacturing_entities.entity_id'), primary_key=True)
    company_name = Column(String(255), nullable=False)
    relationship_type = Column(String(100))
    contract_terms = Column(Text)
    exclusivity_level = Column(String(100))
    capacity_allocation = Column(Text)
    specialization = Column(Text)
    entity = relationship("ManufacturingEntity", back_populates="external_partner")


# --- New Models from Phase 3 ---

class ProcessStage(db.Model):
    __tablename__ = 'process_stages'
    stage_id = Column(Integer, primary_key=True)
    stage_name = Column(String(255), unique=True, nullable=False)
    stage_category = Column(String(255))
    short_description = Column(Text, nullable=True)
    description = Column(Text)
    
    # NEW: Hierarchical structure
    parent_stage_id = Column(Integer, ForeignKey('process_stages.stage_id'))
    hierarchy_level = Column(Integer)  # 1=Phase, 2=Stage, 3=Operation, etc.
    stage_order = Column(Integer)  # Order within parent level
    
    # Relationships
    template_links = relationship("TemplateStage", back_populates="stage")
    product_overrides = relationship("ProductProcessOverride", back_populates="stage")
    technologies = relationship("ManufacturingTechnology", back_populates="stage")
    challenges = relationship("ManufacturingChallenge", back_populates="primary_stage")
    
    # NEW: Self-referential hierarchy
    parent = relationship("ProcessStage", 
                         remote_side=[stage_id],
                         backref="children")
    
        
    @classmethod
    def get_all_fields(cls):
        """Returns a list of all column names for the model."""
        from sqlalchemy import inspect
        return [c.key for c in inspect(cls).attrs if c.key not in ['template_links', 'product_overrides', 'technologies', 'challenges', 'parent', 'children']]
    
    @classmethod
    def get_top_level_phases(cls):
        """Get all Level 1 phases (top of hierarchy)"""
        return cls.query.filter_by(hierarchy_level=1).order_by(cls.stage_order).all()
    
    @classmethod
    def get_by_level(cls, level):
        """Get all stages at a specific hierarchy level"""
        return cls.query.filter_by(hierarchy_level=level).order_by(cls.stage_order).all()
    
    def get_full_path(self):
        """Get the full hierarchical path for this stage"""
        path = [self.stage_name]
        current = self.parent
        while current:
            path.insert(0, current.stage_name)
            current = current.parent
        return " > ".join(path)

class ProcessTemplate(db.Model):
    __tablename__ = 'process_templates'
    template_id = Column(Integer, primary_key=True)
    modality_id = Column(Integer, ForeignKey('modalities.modality_id'))
    template_name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Relationships
    modality = relationship("Modality", back_populates="process_templates")
    stages = relationship("TemplateStage", back_populates="template", cascade="all, delete-orphan")

class TemplateStage(db.Model):
    __tablename__ = 'template_stages'
    template_id = Column(Integer, ForeignKey('process_templates.template_id'), primary_key=True)
    stage_id = Column(Integer, ForeignKey('process_stages.stage_id'), primary_key=True)
    stage_order = Column(Integer)
    is_required = Column(Boolean, default=True)
    base_capabilities = Column(JSONB)
    # Relationships
    template = relationship("ProcessTemplate", back_populates="stages")
    stage = relationship("ProcessStage", back_populates="template_links")

class ProductProcessOverride(db.Model):
    __tablename__ = 'product_process_overrides'
    product_id = Column(Integer, ForeignKey('products.product_id'), primary_key=True)
    stage_id = Column(Integer, ForeignKey('process_stages.stage_id'), primary_key=True)
    override_type = Column(String(50)) # e.g., 'add', 'skip', 'modify'
    additional_capabilities = Column(JSONB)
    notes = Column(Text)
    # Relationships
    product = relationship("Product", back_populates="process_overrides")
    stage = relationship("ProcessStage", back_populates="product_overrides")

class ProductTimeline(db.Model):
    """Track milestones and timeline changes for products"""
    __tablename__ = 'product_timelines'
    
    timeline_id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.product_id'), nullable=False)
    milestone_type = Column(String(100), nullable=False)  # Submission, Approval, Launch, PPQ
    milestone_name = Column(String(255), nullable=False)
    planned_date = Column(Date, nullable=True)
    actual_date = Column(Date, nullable=True)
    variance_days = Column(Integer, nullable=True)
    baseline_plan = Column(String(50), nullable=True)  # AD 2024, AD 2023
    status = Column(String(100), nullable=True)  # On Track, Delayed, Completed
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    product = relationship("Product", backref="timeline_milestones")
    
    @classmethod
    def get_all_fields(cls):
        return [c.key for c in inspect(cls).attrs if c.key not in ['product']]


class ProductRegulatoryFiling(db.Model):
    """Track regulatory submissions by geography and indication"""
    __tablename__ = 'product_regulatory_filings'
    
    filing_id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.product_id'), nullable=False)
    indication = Column(String(255), nullable=False)
    geography = Column(String(100), nullable=False)  # US, China, EU, etc.
    filing_type = Column(String(100), nullable=True)  # NDA, BLA, MAA
    submission_date = Column(Date, nullable=True)
    approval_date = Column(Date, nullable=True)
    status = Column(String(100), nullable=True)  # Submitted, Under Review, Approved
    designations = Column(JSONB, nullable=True)  # Breakthrough Therapy, Orphan Drug, etc.
    regulatory_authority = Column(String(100), nullable=True)  # FDA, EMA, NMPA
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    product = relationship("Product", backref="regulatory_filings")
    
    @classmethod
    def get_all_fields(cls):
        return [c.key for c in inspect(cls).attrs if c.key not in ['product']]


class ProductManufacturingSupplier(db.Model):
    """Detailed supplier tracking for DS/DP/Device partners"""
    __tablename__ = 'product_manufacturing_suppliers'
    
    supplier_id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.product_id'), nullable=False)
    supply_type = Column(String(50), nullable=False)  # DS, DP, Device
    supplier_name = Column(String(255), nullable=False)
    site_name = Column(String(255), nullable=True)
    site_location = Column(String(255), nullable=True)
    role = Column(String(100), nullable=True)  # Primary, Backup, Launch, Commercial
    status = Column(String(100), nullable=True)  # Qualified, Ongoing PPQ, Planned
    technology = Column(String(255), nullable=True)  # Granulation tech, process type
    start_date = Column(Date, nullable=True)
    qualification_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    product = relationship("Product", backref="manufacturing_suppliers")
    
    @classmethod
    def get_all_fields(cls):
        return [c.key for c in inspect(cls).attrs if c.key not in ['product']]

# --- SQL View Mappings ---
# These are unmanaged by Alembic but allow SQLAlchemy to query the views

all_product_requirements_view = Table('all_product_requirements', db.metadata,
    Column('product_id', Integer, primary_key=True),
    Column('required_capability_id', Integer, primary_key=True),
    Column('requirement_level', String),
    Column('is_critical', Boolean),
    Column('requirement_source', String),
    Column('modality_name', String),
    Column('capability_name', String)
)

product_complexity_summary_view = Table('product_complexity_summary', db.metadata,
    Column('product_id', Integer, primary_key=True),
    Column('product_name', String),
    Column('modality_id', Integer),
    Column('modality_name', String),
    Column('expected_launch_year', Integer),
    Column('total_requirements', Integer),
    Column('complexity_score', Integer),
    Column('critical_requirements', Integer),
)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    system_prompt = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    llm_settings = relationship("LLMSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password = pbkdf2_sha256.hash(password)

    def check_password(self, password):
        return pbkdf2_sha256.verify(password, self.password)

class LLMSettings(db.Model):
    __tablename__ = 'llm_settings'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    openai_api_key = Column(String(255), nullable=True)
    anthropic_api_key = Column(String(255), nullable=True)
    google_api_key = Column(String(255), nullable=True)
    ollama_base_url = Column(String(255), nullable=True)
    apollo_client_id = Column(String(255), nullable=True)
    apollo_client_secret = Column(String(length=255), nullable=True)
    user = relationship("User", back_populates="llm_settings")