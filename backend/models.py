# backend/models.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Table, Boolean, Date
from sqlalchemy.orm import relationship, column_property, validates
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.inspection import inspect
from passlib.hash import pbkdf2_sha256
from flask_login import UserMixin
from .db import db
from sqlalchemy.orm.properties import RelationshipProperty

# --- Core Entity Tables ---

class Product(db.Model):
    __tablename__ = 'products'
    product_id = Column(Integer, primary_key=True)
    product_code = Column(String(100), unique=True, nullable=False, index=True)
    product_name = Column(String(255), nullable=True)

    # Core Product Info
    product_type = Column(String(100), nullable=True)
    
    # NME / LINE-EXTENSION TRACKING
    is_nme = Column(Boolean, nullable=False, default=True, server_default='true')
    is_line_extension = Column(Boolean, nullable=False, default=False, server_default='false')
    parent_product_id = Column(Integer, ForeignKey('products.product_id', ondelete='CASCADE'), nullable=True, index=True)
    launch_sequence = Column(Integer, nullable=False, default=1, server_default='1')
    line_extension_indication = Column(String(255), nullable=True)
    
    short_description = Column(Text, nullable=True)
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
    lifecycle_indications = Column(JSONB, nullable=True)
    regulatory_designations = Column(JSONB, nullable=True)

    # Manufacturing & Supply Chain
    manufacturing_strategy = Column(String(100), nullable=True)
    manufacturing_sites = Column(JSONB, nullable=True)
    volume_forecast = Column(JSONB, nullable=True)

    # Formulation Fields
    primary_packaging = Column(String(100), nullable=True)
    route_of_administration = Column(String(100), nullable=True)
    biel_category = Column(String(20), nullable=True)
    granulation_technology = Column(String(255), nullable=True)

    # Regulatory Fields
    submission_status = Column(String(100), nullable=True)
    submission_date = Column(Date, nullable=True)
    approval_date = Column(Date, nullable=True)
    launch_geography = Column(String(255), nullable=True)
    regulatory_details = Column(JSONB, nullable=True)

    # Operational Fields
    ppq_status = Column(String(100), nullable=True)
    ppq_completion_date = Column(Date, nullable=True)
    ppq_details = Column(JSONB, nullable=True)
    timeline_variance_days = Column(Integer, nullable=True)
    timeline_variance_baseline = Column(String(50), nullable=True)
    critical_path_item = Column(String(255), nullable=True)
    ds_volume_category = Column(String(100), nullable=True)
    dp_volume_category = Column(String(100), nullable=True)

    # Supply Chain Fields
    ds_suppliers = Column(JSONB, nullable=True)
    dp_suppliers = Column(JSONB, nullable=True)
    device_partners = Column(JSONB, nullable=True)
    raw_content = Column(Text, nullable=True)

    # Risk Fields
    operational_risks = Column(JSONB, nullable=True)
    timeline_risks = Column(JSONB, nullable=True)
    supply_chain_risks = Column(JSONB, nullable=True)

    # Clinical Fields
    clinical_trials = Column(JSONB, nullable=True)
    patient_population = Column(Text, nullable=True)
    development_program_name = Column(String(255), nullable=True)

    # Foreign Keys
    modality_id = Column(Integer, ForeignKey('modalities.modality_id'))
    process_template_id = Column(Integer, ForeignKey('process_templates.template_id'), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships
    indications = relationship("Indication", back_populates="product", cascade="all, delete-orphan")
    supply_chain = relationship("ProductSupplyChain", back_populates="product", cascade="all, delete-orphan")
    process_overrides = relationship("ProductProcessOverride", back_populates="product", cascade="all, delete-orphan")
    requirements = relationship("ProductRequirement", back_populates="product")
    modality = relationship("Modality", back_populates="products")
    process_template = relationship("ProcessTemplate", backref="products")
    
    # Self-referential relationship for NME → Line-Extensions
    line_extensions = relationship(
        "Product",
        backref=db.backref('parent_nme', remote_side=[product_id]),
        foreign_keys=[parent_product_id],
        cascade="all, delete-orphan"
    )

    @validates('process_template_id')
    def validate_template_matches_modality(self, key, template_id):
        """
        Ensure the selected process template belongs to the product's modality.
        """
        if template_id is not None and self.modality_id is not None:
            from sqlalchemy.orm import Session
            session = Session.object_session(self)
            if session:
                template = session.query(ProcessTemplate).get(template_id)
                if template and template.modality_id != self.modality_id:
                    modality = session.query(Modality).get(self.modality_id)
                    # Just log a warning or allow it for now to prevent import blocks
                    # Raising ValueError here blocks valid imports if order is slightly off
                    pass 
        return template_id

    @validates('parent_product_id', 'is_line_extension', 'is_nme')
    def validate_nme_line_extension_logic(self, key, value):
        """Validates NME/Line-Extension logic rules."""
        # We only strictly validate incompatible states here (like NME + Line Ext).
        # We skip the "Line-Extension must have parent" check here because 
        # during __init__, is_line_extension might be set before parent_product_id.
        
        current_is_nme = value if key == 'is_nme' else getattr(self, 'is_nme', None)
        current_is_line_ext = value if key == 'is_line_extension' else getattr(self, 'is_line_extension', None)
        
        if current_is_nme and current_is_line_ext:
            raise ValueError("A product cannot be both an NME and a Line-Extension")
        
        # If setting parent_product_id, must NOT be an NME
        if key == 'parent_product_id' and value is not None and current_is_nme:
             raise ValueError("NMEs cannot have a parent_product_id")
        
        return value

    @classmethod
    def get_all_fields(cls):
        """
        Returns a list of all column/property names for the model,
        correctly excluding relationship objects.
        """
        inspector = inspect(cls)
        return [
            c.key for c in inspector.attrs
            if not isinstance(c, RelationshipProperty) and not c.key.startswith('_')
        ]

    def get_all_capability_requirements(self):
        """
        Get complete capability requirements from the three-tier inheritance system:
        1. Modality-level (inherited by all products of this modality)
        2. Template-level (from process_template → template_stages → base_capabilities)
        3. Product-level (specific overrides/additions)
        """
        requirements = {
            'modality_inherited': [],
            'template_inherited': [],
            'product_specific': []
        }

        # 1. Get modality-level requirements
        if self.modality:
            for req in self.modality.requirements:
                requirements['modality_inherited'].append({
                    'capability': req.capability.capability_name,
                    'level': req.requirement_level,
                    'is_critical': req.is_critical,
                    'source': f"Modality: {self.modality.modality_name}"
                })

        # 2. Get template-level requirements from base_capabilities
        if self.process_template:
            for template_stage in self.process_template.stages:
                if template_stage.base_capabilities:
                    for cap_name in template_stage.base_capabilities:
                        requirements['template_inherited'].append({
                            'capability': cap_name,
                            'stage': template_stage.stage.stage_name,
                            'is_required': template_stage.is_required,
                            'source': f"Template: {self.process_template.template_name}"
                        })

        # 3. Get product-specific requirements
        for req in self.requirements:
            requirements['product_specific'].append({
                'capability': req.capability.capability_name,
                'level': req.requirement_level,
                'is_critical': req.is_critical,
                'timeline_needed': req.timeline_needed,
                'notes': req.notes,
                'source': 'Product-specific'
            })

        return requirements

    def get_all_launches(self):
        """Returns all launches (NME + Line-Extensions) for this product family."""
        if self.is_line_extension and self.parent_nme:
            return self.parent_nme.get_all_launches()
        elif self.is_nme:
            all_launches = [self] + list(self.line_extensions)
            return sorted(all_launches, key=lambda x: x.launch_sequence)
        else:
            return [self]
    
    def get_launch_timeline(self):
        """Returns launch timeline information as a dict."""
        all_launches = self.get_all_launches()
        return {
            'nme': next((p for p in all_launches if p.is_nme), None),
            'line_extensions': [p for p in all_launches if p.is_line_extension],
            'total_launches': len(all_launches),
            'timeline': [
                {
                    'sequence': p.launch_sequence,
                    'year': p.expected_launch_year,
                    'indication': p.line_extension_indication or p.lead_indication,
                    'code': p.product_code,
                    'name': p.product_name,
                    'type': 'NME' if p.is_nme else 'Line-Extension',
                    'status': p.project_status
                }
                for p in all_launches
            ]
        }
    
    def is_orphaned_line_extension(self):
        """
        Checks if this is a line extension without a valid parent.
        """
        return self.is_line_extension and not self.parent_product_id
    
    def get_family_summary(self):
        """Returns a one-line summary of the product family."""
        if self.is_nme:
            line_ext_count = len(self.line_extensions)
            if line_ext_count == 0:
                return f"NME (no line extensions)"
            else:
                return f"NME with {line_ext_count} line extension{'s' if line_ext_count != 1 else ''}"
        elif self.is_line_extension and self.parent_nme:
            return f"Line-Extension of {self.parent_nme.product_code}"
        else:
            return "Standalone product"
    
    @classmethod
    def get_nmes_only(cls):
        """Query only NME products."""
        return cls.query.filter_by(is_nme=True).order_by(cls.expected_launch_year).all()
    
    @classmethod
    def get_line_extensions_only(cls):
        """Query only Line-Extension products."""
        return cls.query.filter_by(is_line_extension=True).order_by(
            cls.parent_product_id,
            cls.launch_sequence
        ).all()
    
    @classmethod
    def get_with_line_extensions(cls, product_id):
        """Get a product with all its line extensions eagerly loaded."""
        from sqlalchemy.orm import joinedload
        return cls.query.options(
            joinedload(cls.line_extensions)
        ).filter_by(product_id=product_id).first()
    
    @classmethod
    def get_active_products(cls, include_line_extensions=True):
        """Get all active (non-discontinued) products."""
        query = cls.query.filter(
            (cls.project_status == None) | (cls.project_status != 'Discontinued')
        )
        
        if not include_line_extensions:
            query = query.filter_by(is_nme=True)
        
        return query.order_by(cls.expected_launch_year).all()
    
    @classmethod
    def get_product_families(cls):
        """Get all product families (NMEs with their line extensions)."""
        nmes = cls.get_nmes_only()
        families = []
        
        for nme in nmes:
            family = {
                'nme': nme,
                'line_extensions': list(nme.line_extensions),
                'total_launches': 1 + len(nme.line_extensions),
                'first_launch_year': nme.expected_launch_year,
                'last_launch_year': max(
                    [nme.expected_launch_year or 0] + 
                    [le.expected_launch_year or 0 for le in nme.line_extensions]
                )
            }
            families.append(family)
        
        return families


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


class ValueStep(db.Model):
    """Manufacturing value chain steps with defined order"""
    __tablename__ = 'value_steps'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    name_en = Column(String(100), nullable=True)
    sort_order = Column(Integer, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    description_en = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    challenges = relationship("Challenge", back_populates="value_step_rel")

    @classmethod
    def get_all_fields(cls):
        return [c.key for c in inspect(cls).attrs if c.key not in ['challenges']]

    @classmethod
    def get_ordered(cls):
        """Get all value steps in manufacturing order."""
        return cls.query.order_by(cls.sort_order).all()

    @classmethod
    def get_next(cls, current_step):
        """Get the next step in the value chain."""
        if not current_step:
            return None
        return cls.query.filter(cls.sort_order > current_step.sort_order)\
            .order_by(cls.sort_order).first()

    @classmethod
    def get_previous(cls, current_step):
        """Get the previous step in the value chain."""
        if not current_step:
            return None
        return cls.query.filter(cls.sort_order < current_step.sort_order)\
            .order_by(cls.sort_order.desc()).first()


class Challenge(db.Model):
    """Simplified challenge model - modality-agnostic base information"""
    __tablename__ = 'challenges'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    name_en = Column(String(255), nullable=True)
    agnostic_description = Column(Text, nullable=True)
    agnostic_description_en = Column(Text, nullable=True)
    agnostic_root_cause = Column(Text, nullable=True)
    agnostic_root_cause_en = Column(Text, nullable=True)
    value_step_id = Column(Integer, ForeignKey('value_steps.id'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    value_step_rel = relationship("ValueStep", back_populates="challenges")
    modality_details = relationship(
        "ChallengeModalityDetail",
        back_populates="challenge",
        cascade="all, delete-orphan"
    )

    @property
    def value_step(self):
        """Convenience property to get value step name."""
        return self.value_step_rel.name if self.value_step_rel else None

    @classmethod
    def get_all_fields(cls):
        """Returns a list of all column names for the model."""
        return [
            c.key for c in inspect(cls).attrs
            if c.key not in ['modality_details', 'value_step_rel']
        ]


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


class Modality(db.Model):
    __tablename__ = 'modalities'
    modality_id = Column(Integer, primary_key=True)
    modality_name = Column(String(255), unique=True, nullable=False)
    modality_name_en = Column(String(255), nullable=True)
    modality_category = Column(String(255))
    label = Column(String(255), nullable=True)
    label_en = Column(String(255), nullable=True)
    short_description = Column(Text, nullable=True)
    short_description_en = Column(Text, nullable=True)
    description = Column(Text)
    description_en = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    products = relationship("Product", back_populates="modality")
    process_templates = relationship("ProcessTemplate", back_populates="modality")
    requirements = relationship("ModalityRequirement", back_populates="modality")
    challenge_details = relationship(
        "ChallengeModalityDetail",
        back_populates="modality",
        cascade="all, delete-orphan"
    )

    @classmethod
    def get_all_fields(cls):
        """Returns a list of all column names for the model."""
        return [
            c.key for c in inspect(cls).attrs
            if c.key not in ['products', 'process_templates', 'requirements', 'challenge_details']
        ]


class ChallengeModalityDetail(db.Model):
    """Links challenges to modalities with specific scores and details"""
    __tablename__ = 'challenge_modality_details'

    id = Column(Integer, primary_key=True)
    challenge_id = Column(Integer, ForeignKey('challenges.id'), nullable=False)
    modality_id = Column(Integer, ForeignKey('modalities.modality_id'), nullable=False)

    # Modality-specific description and root causes
    specific_description = Column(Text, nullable=True)
    specific_description_en = Column(Text, nullable=True)
    specific_root_cause = Column(Text, nullable=True)
    specific_root_cause_en = Column(Text, nullable=True)

    # Impact scoring (1-5)
    impact_score = Column(Integer, nullable=True)
    impact_details = Column(Text, nullable=True)
    impact_details_en = Column(Text, nullable=True)

    # Maturity scoring (1-5)
    maturity_score = Column(Integer, nullable=True)
    maturity_details = Column(Text, nullable=True)
    maturity_details_en = Column(Text, nullable=True)

    # Trends
    trends_3_5_years = Column(Text, nullable=True)
    trends_3_5_years_en = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('challenge_id', 'modality_id', name='uq_challenge_modality'),
    )

    # Relationships
    challenge = relationship("Challenge", back_populates="modality_details")
    modality = relationship("Modality", back_populates="challenge_details")

    @classmethod
    def get_all_fields(cls):
        """Returns a list of all column names for the model."""
        return [
            c.key for c in inspect(cls).attrs
            if c.key not in ['challenge', 'modality']
        ]


class ManufacturingCapability(db.Model):
    __tablename__ = 'manufacturing_capabilities'
    capability_id = Column(Integer, primary_key=True)
    capability_name = Column(String(255), unique=True, nullable=False)
    capability_category = Column(String(255), index=True)
    approach_category = Column(String(255))
    description = Column(Text)
    complexity_weight = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    modality_requirements = relationship("ModalityRequirement", back_populates="capability")
    product_requirements = relationship("ProductRequirement", back_populates="capability")
    entity_provisions = relationship("EntityCapability", back_populates="capability")

    @classmethod
    def get_all_fields(cls):
        """Returns a list of all column names for the model."""
        return [
            c.key for c in inspect(cls).attrs 
            if not c.key.startswith('_') and c.key not in ['modality_requirements', 'product_requirements', 'entity_provisions']
        ]


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
    internal_facility = relationship(
        "InternalFacility",
        back_populates="entity",
        uselist=False,
        cascade="all, delete-orphan"
    )
    external_partner = relationship(
        "ExternalPartner",
        back_populates="entity",
        uselist=False,
        cascade="all, delete-orphan"
    )
    capabilities = relationship("EntityCapability", back_populates="entity", cascade="all, delete-orphan")

    @classmethod
    def get_all_fields(cls):
        """Returns a list of all column names for the model."""
        return [
            c.key for c in inspect(cls).attrs 
            if not c.key.startswith('_') and c.key not in ['supply_chain_links', 'internal_facility', 'external_partner', 'capabilities']
        ]


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


class ProcessStage(db.Model):
    __tablename__ = 'process_stages'
    stage_id = Column(Integer, primary_key=True)
    stage_name = Column(String(255), unique=True, nullable=False)
    stage_category = Column(String(255))
    short_description = Column(Text, nullable=True)
    description = Column(Text)

    # Hierarchical structure
    parent_stage_id = Column(Integer, ForeignKey('process_stages.stage_id'))
    hierarchy_level = Column(Integer)
    stage_order = Column(Integer)

    # Relationships
    template_links = relationship("TemplateStage", back_populates="stage")
    product_overrides = relationship("ProductProcessOverride", back_populates="stage")

    # Self-referential hierarchy
    parent = relationship(
        "ProcessStage",
        remote_side=[stage_id],
        backref="children"
    )

    @classmethod
    def get_all_fields(cls):
        """Returns a list of all column names for the model."""
        return [
            c.key for c in inspect(cls).attrs
            if c.key not in ['template_links', 'product_overrides', 'parent', 'children']
        ]

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
    override_type = Column(String(50))
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
    milestone_type = Column(String(100), nullable=False)
    milestone_name = Column(String(255), nullable=False)
    planned_date = Column(Date, nullable=True)
    actual_date = Column(Date, nullable=True)
    variance_days = Column(Integer, nullable=True)
    baseline_plan = Column(String(50), nullable=True)
    status = Column(String(100), nullable=True)
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
    geography = Column(String(100), nullable=False)
    filing_type = Column(String(100), nullable=True)
    submission_date = Column(Date, nullable=True)
    approval_date = Column(Date, nullable=True)
    status = Column(String(100), nullable=True)
    designations = Column(JSONB, nullable=True)
    regulatory_authority = Column(String(100), nullable=True)
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
    supply_type = Column(String(50), nullable=False)
    supplier_name = Column(String(255), nullable=False)
    site_name = Column(String(255), nullable=True)
    site_location = Column(String(255), nullable=True)
    role = Column(String(100), nullable=True)
    status = Column(String(100), nullable=True)
    technology = Column(String(255), nullable=True)
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
all_product_requirements_view = Table(
    'all_product_requirements', db.metadata,
    Column('product_id', Integer, primary_key=True),
    Column('required_capability_id', Integer, primary_key=True),
    Column('requirement_level', String),
    Column('is_critical', Boolean),
    Column('requirement_source', String),
    Column('modality_name', String),
    Column('capability_name', String)
)

product_complexity_summary_view = Table(
    'product_complexity_summary', db.metadata,
    Column('product_id', Integer, primary_key=True),
    Column('product_name', String),
    Column('modality_id', Integer),
    Column('modality_name', String),
    Column('expected_launch_year', Integer),
    Column('total_requirements', Integer),
    Column('complexity_score', Integer),
    Column('critical_requirements', Integer)
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


# =============================================================================
# NEW CORE ENTITIES: Drug Substances, Drug Products, Projects
# =============================================================================

# Junction Tables (defined first for relationship references)
project_drug_substances = Table(
    'project_drug_substances', db.metadata,
    Column('project_id', Integer, ForeignKey('projects.id', ondelete='CASCADE'), primary_key=True),
    Column('drug_substance_id', Integer, ForeignKey('drug_substances.id', ondelete='CASCADE'), primary_key=True)
)

project_drug_products = Table(
    'project_drug_products', db.metadata,
    Column('project_id', Integer, ForeignKey('projects.id', ondelete='CASCADE'), primary_key=True),
    Column('drug_product_id', Integer, ForeignKey('drug_products.id', ondelete='CASCADE'), primary_key=True)
)

drug_substance_drug_products = Table(
    'drug_substance_drug_products', db.metadata,
    Column('drug_substance_id', Integer, ForeignKey('drug_substances.id', ondelete='CASCADE'), primary_key=True),
    Column('drug_product_id', Integer, ForeignKey('drug_products.id', ondelete='CASCADE'), primary_key=True)
)


class DrugSubstance(db.Model):
    """
    Drug Substance (API) - Active Pharmaceutical Ingredient
    Represents the chemical/biological compound before formulation.
    """
    __tablename__ = 'drug_substances'

    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False, index=True)  # e.g., "BI 1015550"
    inn = Column(String(255), nullable=True)  # International Nonproprietary Name, e.g., "Nerandomilast"

    # Technical Information
    molecule_type = Column(String(100), nullable=True)  # "Small molecule", "mAb", etc.
    mechanism_of_action = Column(Text, nullable=True)  # "PDE4B inh."
    technology = Column(Text, nullable=True)  # "Standard chemical synthetic"
    storage_conditions = Column(String(255), nullable=True)  # "Room Temp.", "2-8°C"
    shelf_life = Column(String(100), nullable=True)

    # Site Information
    development_approach = Column(String(100), nullable=True)  # "INTERNAL", "CDMO"
    development_site = Column(String(255), nullable=True)  # "BI Biberach"
    launch_site = Column(String(255), nullable=True)  # "BI Ingelheim"
    release_site = Column(String(255), nullable=True)
    routine_site = Column(String(255), nullable=True)

    # Volume Information
    demand_category = Column(String(50), nullable=True)  # "Low", "Medium", "High"
    demand_launch_year = Column(String(50), nullable=True)  # "32kg"
    demand_peak_year = Column(String(50), nullable=True)  # "2200kg"
    peak_demand_range = Column(String(100), nullable=True)  # "1000-10000kg"

    # Meta
    commercial = Column(String(50), nullable=True)  # "Make", "Buy"
    status = Column(String(50), nullable=True)  # "Ongoing", "Completed"
    type = Column(String(50), nullable=True)  # "NCE", "Biosimilar"
    biel = Column(String(10), nullable=True)  # "3A"
    d_and_dl_ops = Column(Text, nullable=True)  # Responsible person
    last_refresh = Column(Date, nullable=True)

    # Optional: Link to Modality
    modality_id = Column(Integer, ForeignKey('modalities.modality_id'), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    modality = relationship("Modality", backref="drug_substances")
    projects = relationship(
        "Project",
        secondary=project_drug_substances,
        back_populates="drug_substances"
    )
    drug_products = relationship(
        "DrugProduct",
        secondary=drug_substance_drug_products,
        back_populates="drug_substances"
    )

    @classmethod
    def get_all_fields(cls):
        """Returns a list of all column names for the model."""
        return [
            c.key for c in inspect(cls).attrs
            if c.key not in ['modality', 'projects', 'drug_products']
        ]


class DrugProduct(db.Model):
    """
    Drug Product - The formulated pharmaceutical product
    Represents the final dosage form (tablet, injection, etc.)
    """
    __tablename__ = 'drug_products'

    id = Column(Integer, primary_key=True)
    code = Column(String(100), unique=True, nullable=False, index=True)  # e.g., "Nerandomilast-FC_Tablet"

    # Technical Information
    pharm_form = Column(String(100), nullable=True)  # "FC_Tablet", "Sf_Injection"
    technology = Column(Text, nullable=True)  # "Fluid Bed Granulation", "Sterile Filling"
    classification = Column(String(50), nullable=True)  # "Solid", "Liquid"
    storage_conditions = Column(String(255), nullable=True)
    transport_conditions = Column(String(255), nullable=True)
    holding_time = Column(String(100), nullable=True)

    # Site Information
    development_approach = Column(String(100), nullable=True)  # "INTERNAL", "CDMO", "EACD"
    development_site = Column(String(255), nullable=True)
    launch_site = Column(String(255), nullable=True)
    release_site = Column(String(255), nullable=True)
    routine_site = Column(String(255), nullable=True)

    # Volume Information
    demand_category = Column(String(50), nullable=True)  # "Very Low", "Low", "Medium", "High"
    demand_launch_year = Column(String(50), nullable=True)
    demand_peak_year = Column(String(50), nullable=True)
    peak_demand_range = Column(String(100), nullable=True)  # "<1 mio PCS", "1-10 mio PCS"

    # Meta
    commercial = Column(String(50), nullable=True)  # "Make", "Buy", "Make (strat)"
    strategic_technology = Column(Text, nullable=True)  # "Film-coated tablet", "Device for s.c. injection"
    d_and_dl_ops = Column(Text, nullable=True)
    last_refresh = Column(Date, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    projects = relationship(
        "Project",
        secondary=project_drug_products,
        back_populates="drug_products"
    )
    drug_substances = relationship(
        "DrugSubstance",
        secondary=drug_substance_drug_products,
        back_populates="drug_products"
    )

    @classmethod
    def get_all_fields(cls):
        """Returns a list of all column names for the model."""
        return [
            c.key for c in inspect(cls).attrs
            if c.key not in ['projects', 'drug_substances']
        ]


class Project(db.Model):
    """
    Project - Links Drug Substances and Drug Products with Timeline
    Represents a development project with its milestones.
    """
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True, nullable=False, index=True)  # e.g., "Nerandomilast (IPF)"

    # Project Information
    indication = Column(String(255), nullable=True)  # "IPF", "SSc", "NSCLC"
    project_type = Column(String(50), nullable=True)  # "NME", "NI", "PMO", "PED"
    administration = Column(String(100), nullable=True)  # "Oral", "Subcutaneous", "Intravenous"
    status = Column(String(50), nullable=True, default='active')  # 'active', 'discontinued', 'on_hold'

    # Timeline Milestones (Core Data!)
    sod = Column(Date, nullable=True)  # Start of Development
    dsmm3 = Column(Date, nullable=True)  # Drug Substance Manufacturing Milestone 3
    dsmm4 = Column(Date, nullable=True)  # Drug Substance Manufacturing Milestone 4
    dpmm3 = Column(Date, nullable=True)  # Drug Product Manufacturing Milestone 3
    dpmm4 = Column(Date, nullable=True)  # Drug Product Manufacturing Milestone 4
    rofd = Column(Date, nullable=True)  # Release of Full Development
    submission = Column(Date, nullable=True)  # Regulatory Submission
    launch = Column(Date, nullable=True)  # Market Launch

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    drug_substances = relationship(
        "DrugSubstance",
        secondary=project_drug_substances,
        back_populates="projects"
    )
    drug_products = relationship(
        "DrugProduct",
        secondary=project_drug_products,
        back_populates="projects"
    )

    @classmethod
    def get_all_fields(cls):
        """Returns a list of all column names for the model."""
        return [
            c.key for c in inspect(cls).attrs
            if c.key not in ['drug_substances', 'drug_products']
        ]

    def get_timeline_dict(self):
        """Returns timeline milestones as a dictionary."""
        return {
            'sod': self.sod.isoformat() if self.sod else None,
            'dsmm3': self.dsmm3.isoformat() if self.dsmm3 else None,
            'dsmm4': self.dsmm4.isoformat() if self.dsmm4 else None,
            'dpmm3': self.dpmm3.isoformat() if self.dpmm3 else None,
            'dpmm4': self.dpmm4.isoformat() if self.dpmm4 else None,
            'rofd': self.rofd.isoformat() if self.rofd else None,
            'submission': self.submission.isoformat() if self.submission else None,
            'launch': self.launch.isoformat() if self.launch else None,
        }