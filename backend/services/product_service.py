# backend/services/product_service.py
from sqlalchemy.orm import joinedload
from ..models import Product, Modality, ProcessTemplate, all_product_requirements_view
from ..db import db


def get_all_products():
    """Get all products, eagerly loading the modality relationship to prevent N+1 queries."""
    return Product.query.options(joinedload(Product.modality)).order_by(Product.product_code).all()


def get_product_table_context(requested_columns_str: str = None):
    """Prepares the full context for the dynamic product table with correct relationship handling."""

    DEFAULT_COLUMNS = [
        'modality_name', 'process_template_name', 'product_code',
        'product_name', 'short_description', 'therapeutic_area', 'current_phase'
    ]

    all_fields = Product.get_all_fields()

    if 'modality_id' in all_fields:
        all_fields.remove('modality_id')
    if 'process_template_id' in all_fields:
        all_fields.remove('process_template_id')

    all_fields.insert(0, 'modality_name')
    all_fields.insert(1, 'process_template_name')

    if requested_columns_str:
        selected_fields = [col for col in requested_columns_str.split(',') if col in all_fields]
    else:
        selected_fields = DEFAULT_COLUMNS

    if not selected_fields:
        selected_fields = DEFAULT_COLUMNS

    products = Product.query.options(
        joinedload(Product.modality),
        joinedload(Product.process_template)
    ).order_by(Product.product_code).all()

    product_dicts = []
    for p in products:
        item_data = {}
        for field in all_fields:
            if field == 'modality_name':
                item_data[field] = p.modality.modality_name if p.modality else 'N/A'
            elif field == 'process_template_name':
                item_data[field] = p.process_template.template_name if p.process_template else 'N/A'
            else:
                item_data[field] = getattr(p, field, None)
        product_dicts.append(item_data)

    return {
        'products': product_dicts,
        'all_fields': all_fields,
        'selected_fields': selected_fields,
        'entity_type': 'product',
        'entity_plural': 'products',
        'table_id': 'productsTable'
    }


def inline_update_product_field(product_id: int, field: str, value):
    """Updates a single field on a product for inline editing."""

    product = Product.query.get(product_id)
    if not product:
        return None, "Product not found."

    if not hasattr(product, field) and field not in ['modality_name', 'process_template_name']:
        return None, f"Field '{field}' does not exist."

    try:
        if field == 'modality_name':
            if value and value.strip():
                modality = Modality.query.filter_by(modality_name=value.strip()).first()
                if not modality:
                    return None, f"Modality '{value.strip()}' not found."
                product.modality_id = modality.modality_id

                if product.process_template_id:
                    old_template = ProcessTemplate.query.get(product.process_template_id)
                    if old_template and old_template.modality_id != modality.modality_id:
                        product.process_template_id = None
            else:
                product.modality_id = None
                product.process_template_id = None

        elif field == 'process_template_name':
            if value and value.strip():
                template = ProcessTemplate.query.filter_by(template_name=value.strip()).first()
                if not template:
                    return None, f"Process template '{value.strip()}' not found."

                if product.modality_id and template.modality_id != product.modality_id:
                    modality = Modality.query.get(product.modality_id)
                    return None, (
                        f"Template '{template.template_name}' does not belong to "
                        f"modality '{modality.modality_name if modality else 'Unknown'}'"
                    )

                product.process_template_id = template.template_id
            else:
                product.process_template_id = None

        elif field == 'product_code':
            if not value or not str(value).strip():
                return None, "Product Code cannot be empty."
            product.product_code = str(value).strip()
        else:
            setattr(product, field, value)

        db.session.commit()
        return product, f"Updated {field} successfully."

    except ValueError as e:
        db.session.rollback()
        return None, str(e)
    except Exception as e:
        db.session.rollback()
        return None, f"Update failed: {str(e)}"


def get_product_with_requirements(product_id: int):
    """Gets a single product and eagerly loads its combined requirements."""

    product = Product.query.options(
        joinedload(Product.modality)
    ).get(product_id)

    if not product:
        return None, None

    requirements = db.session.query(all_product_requirements_view).filter_by(product_id=product_id).all()
    return product, requirements


def get_products_by_modality(modality_id: int):
    """Gets all products for a specific modality."""
    return Product.query.filter(Product.modality_id == modality_id).order_by(Product.product_name).all()


def get_nme_products(active_only=True):
    """
    Get all NME products, optionally filtered by active status.
    
    Args:
        active_only: If True, excludes discontinued products
        
    Returns:
        list: NME Product objects with modality loaded
    """
    query = Product.query.filter_by(is_nme=True).options(
        joinedload(Product.modality),
        joinedload(Product.process_template)
    )
    
    if active_only:
        query = query.filter(
            (Product.project_status == None) | (Product.project_status != 'Discontinued')
        )
    
    return query.order_by(Product.expected_launch_year).all()


def get_line_extension_products(parent_product_id=None, active_only=True):
    """
    Get Line-Extension products, optionally for a specific parent.
    
    Args:
        parent_product_id: If provided, only returns line extensions of this parent
        active_only: If True, excludes discontinued products
        
    Returns:
        list: Line-Extension Product objects
    """
    query = Product.query.filter_by(is_line_extension=True).options(
        joinedload(Product.modality),
        joinedload(Product.parent_nme)
    )
    
    if parent_product_id:
        query = query.filter_by(parent_product_id=parent_product_id)
    
    if active_only:
        query = query.filter(
            (Product.project_status == None) | (Product.project_status != 'Discontinued')
        )
    
    return query.order_by(Product.parent_product_id, Product.launch_sequence).all()


def get_product_family(product_id):
    """
    Get a complete product family (NME + all line extensions).
    
    Args:
        product_id: The ID of any product in the family (NME or Line-Extension)
        
    Returns:
        dict: {
            'nme': Product object,
            'line_extensions': list of Product objects,
            'total_launches': int,
            'timeline': list of launch info dicts
        }
    """
    product = Product.query.get(product_id)
    
    if not product:
        return None
    
    return product.get_launch_timeline()


def get_all_product_families(active_only=True):
    """
    Get all product families with their complete launch timelines.
    
    Args:
        active_only: If True, excludes discontinued products
        
    Returns:
        list: List of family dicts, each containing NME + line extensions
    """
    nmes = get_nme_products(active_only=active_only)
    
    families = []
    for nme in nmes:
        family = {
            'nme': nme,
            'line_extensions': [
                le for le in nme.line_extensions
                if not active_only or (le.project_status != 'Discontinued')
            ],
            'total_launches': None,
            'first_launch_year': nme.expected_launch_year,
            'last_launch_year': None
        }
        
        family['total_launches'] = 1 + len(family['line_extensions'])
        
        all_years = [nme.expected_launch_year or 0] + [
            le.expected_launch_year or 0 
            for le in family['line_extensions']
        ]
        family['last_launch_year'] = max(all_years) if all_years else None
        
        families.append(family)
    
    return families


def get_products_by_launch_year(year, include_line_extensions=True, active_only=True):
    """
    Get all products launching in a specific year.
    
    Args:
        year: The launch year to filter by
        include_line_extensions: If False, returns only NMEs
        active_only: If True, excludes discontinued products
        
    Returns:
        list: Product objects launching in the specified year
    """
    query = Product.query.filter_by(expected_launch_year=year).options(
        joinedload(Product.modality),
        joinedload(Product.parent_nme)
    )
    
    if not include_line_extensions:
        query = query.filter_by(is_nme=True)
    
    if active_only:
        query = query.filter(
            (Product.project_status == None) | (Product.project_status != 'Discontinued')
        )
    
    return query.order_by(Product.launch_sequence).all()


def get_pipeline_summary(active_only=True):
    """
    Get a comprehensive summary of the pipeline.
    
    Args:
        active_only: If True, excludes discontinued products
        
    Returns:
        dict: Pipeline statistics and groupings
    """
    if active_only:
        products = Product.query.filter(
            (Product.project_status == None) | (Product.project_status != 'Discontinued')
        ).all()
    else:
        products = Product.query.all()
    
    nme_count = sum(1 for p in products if p.is_nme)
    line_ext_count = sum(1 for p in products if p.is_line_extension)
    
    by_year = {}
    for product in products:
        if product.expected_launch_year:
            year = product.expected_launch_year
            if year not in by_year:
                by_year[year] = {'nmes': [], 'line_extensions': [], 'total': 0}
            
            if product.is_nme:
                by_year[year]['nmes'].append(product)
            else:
                by_year[year]['line_extensions'].append(product)
            
            by_year[year]['total'] += 1
    
    families = get_all_product_families(active_only=active_only)
    
    return {
        'total_products': len(products),
        'nme_count': nme_count,
        'line_extension_count': line_ext_count,
        'product_families': len(families),
        'by_year': dict(sorted(by_year.items())),
        'earliest_launch': min((p.expected_launch_year for p in products if p.expected_launch_year), default=None),
        'latest_launch': max((p.expected_launch_year for p in products if p.expected_launch_year), default=None),
    }


def validate_line_extension_data(data):
    """
    Validates data for creating a line extension.
    
    Args:
        data: dict with line extension data
        
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if not data.get('parent_product_id'):
        return False, "parent_product_id is required for line extensions"
    
    parent = Product.query.get(data['parent_product_id'])
    if not parent:
        return False, f"Parent product with ID {data['parent_product_id']} not found"
    
    if not parent.is_nme:
        return False, f"Parent product {parent.product_code} is not an NME"
    
    if not data.get('line_extension_indication'):
        return False, "line_extension_indication is required for line extensions"
    
    if 'launch_sequence' in data:
        if data['launch_sequence'] <= 1:
            return False, "launch_sequence for line extensions must be > 1"
        
        existing = Product.query.filter_by(
            parent_product_id=data['parent_product_id'],
            launch_sequence=data['launch_sequence']
        ).first()
        
        if existing and existing.product_id != data.get('product_id'):
            return False, f"Launch sequence {data['launch_sequence']} already exists for this parent"
    
    return True, None


def create_line_extension(parent_product_id, line_extension_data):
    """
    Creates a new line extension for an existing NME product.
    
    Args:
        parent_product_id: The ID of the parent NME product
        line_extension_data: dict with line extension properties
        
    Returns:
        tuple: (Product object or None, success_message or error_message)
    """
    parent = Product.query.get(parent_product_id)
    if not parent:
        return None, f"Parent product with ID {parent_product_id} not found"
    
    if not parent.is_nme:
        return None, f"Parent product {parent.product_code} is not an NME"
    
    max_sequence = db.session.query(db.func.max(Product.launch_sequence)).filter_by(
        parent_product_id=parent_product_id
    ).scalar() or 1
    
    next_sequence = max_sequence + 1
    
    try:
        line_ext = Product(
            product_code=line_extension_data['product_code'],
            product_name=line_extension_data.get('product_name'),
            is_nme=False,
            is_line_extension=True,
            parent_product_id=parent_product_id,
            launch_sequence=next_sequence,
            line_extension_indication=line_extension_data['line_extension_indication'],
            expected_launch_year=line_extension_data.get('expected_launch_year'),
            modality_id=parent.modality_id,
            process_template_id=parent.process_template_id,
            short_description=line_extension_data.get('short_description'),
            therapeutic_area=line_extension_data.get('therapeutic_area') or parent.therapeutic_area,
            mechanism_of_action=parent.mechanism_of_action,
            dosage_form=parent.dosage_form,
            route_of_administration=parent.route_of_administration,
        )
        
        db.session.add(line_ext)
        db.session.commit()
        
        return line_ext, f"Line extension {line_ext.product_code} created successfully"
        
    except Exception as e:
        db.session.rollback()
        return None, f"Failed to create line extension: {str(e)}"