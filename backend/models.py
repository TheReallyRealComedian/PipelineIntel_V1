# backend/models.py
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from passlib.hash import pbkdf2_sha256
from flask_login import UserMixin

Base = declarative_base()

# --- Association Tables for Many-to-Many Relationships ---

product_to_challenge_association = Table('product_to_challenge', Base.metadata,
    Column('product_id', Integer, ForeignKey('products.product_id'), primary_key=True),
    Column('challenge_id', Integer, ForeignKey('manufacturing_challenges.challenge_id'), primary_key=True)
)

product_to_technology_association = Table('product_to_technology', Base.metadata,
    Column('product_id', Integer, ForeignKey('products.product_id'), primary_key=True),
    Column('technology_id', Integer, ForeignKey('manufacturing_technologies.technology_id'), primary_key=True)
)

# --- Core Entity Tables ---

class Product(Base):
    __tablename__ = 'products'
    product_id = Column(Integer, primary_key=True)
    product_code = Column(String(100), unique=True, nullable=False, index=True)
    product_name = Column(String(255), nullable=True)
    product_type = Column(String(100), nullable=True)
    base_technology = Column(String(255), nullable=True)
    mechanism_of_action = Column(Text, nullable=True)
    dosage_form = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    indications = relationship("Indication", back_populates="product", cascade="all, delete-orphan")
    supply_chain = relationship("ProductSupplyChain", back_populates="product", cascade="all, delete-orphan")
    
    challenges = relationship("ManufacturingChallenge", secondary=product_to_challenge_association, back_populates="products")
    technologies = relationship("ManufacturingTechnology", secondary=product_to_technology_association, back_populates="products")

    def __repr__(self):
        return f"<Product(product_code='{self.product_code}')>"

class Indication(Base):
    __tablename__ = 'indications'
    indication_id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.product_id'), nullable=False)
    indication_name = Column(String(255), nullable=False)
    therapeutic_area = Column(String(255), nullable=True)
    development_phase = Column(String(100), nullable=True)
    expected_launch_year = Column(Integer, nullable=True)

    product = relationship("Product", back_populates="indications")

    def __repr__(self):
        return f"<Indication(name='{self.indication_name}', product_id={self.product_id})>"

class ManufacturingChallenge(Base):
    __tablename__ = 'manufacturing_challenges'
    challenge_id = Column(Integer, primary_key=True)
    challenge_category = Column(String(255), nullable=False, index=True)
    challenge_name = Column(String(255), unique=True, nullable=False)
    explanation = Column(Text, nullable=True)

    products = relationship("Product", secondary=product_to_challenge_association, back_populates="challenges")

    def __repr__(self):
        return f"<ManufacturingChallenge(name='{self.challenge_name}')>"

class ManufacturingTechnology(Base):
    __tablename__ = 'manufacturing_technologies'
    technology_id = Column(Integer, primary_key=True)
    technology_name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)

    products = relationship("Product", secondary=product_to_technology_association, back_populates="technologies")

    def __repr__(self):
        return f"<ManufacturingTechnology(name='{self.technology_name}')>"

class Partner(Base):
    __tablename__ = 'partners'
    partner_id = Column(Integer, primary_key=True)
    partner_name = Column(String(255), unique=True, nullable=False)
    specialization = Column(Text, nullable=True)
    
    supply_chain_links = relationship("ProductSupplyChain", back_populates="partner")

    def __repr__(self):
        return f"<Partner(name='{self.partner_name}')>"

class ProductSupplyChain(Base):
    __tablename__ = 'product_supply_chain'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.product_id'), nullable=False)
    manufacturing_stage = Column(String(255), nullable=False)
    supply_model = Column(String(100), nullable=True)
    partner_id = Column(Integer, ForeignKey('partners.partner_id'), nullable=True)
    internal_site_name = Column(String(255), nullable=True)

    product = relationship("Product", back_populates="supply_chain")
    partner = relationship("Partner", back_populates="supply_chain_links")
    
# --- User and Settings Tables (Simplified) ---

class User(UserMixin, Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    llm_settings = relationship("LLMSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password = pbkdf2_sha256.hash(password)

    def check_password(self, password):
        return pbkdf2_sha256.verify(password, self.password)

class LLMSettings(Base):
    __tablename__ = 'llm_settings'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    # We can keep these fields for potential future LLM integrations
    openai_api_key = Column(String(255), nullable=True)
    anthropic_api_key = Column(String(255), nullable=True)
    google_api_key = Column(String(255), nullable=True)
    ollama_base_url = Column(String(255), nullable=True)
    apollo_client_id = Column(String(255), nullable=True)
    apollo_client_secret = Column(String(length=255), nullable=True)

    user = relationship("User", back_populates="llm_settings")