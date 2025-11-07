"""
Pipeline Timeline Service

Provides data aggregation and transformation for the pipeline timeline visualization.
Supports flexible configurations for timeline axes, groupings, and display modes.
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..models import Product, Modality, db


class PipelineTimelineService:
    """Service for generating pipeline timeline data based on configuration."""
    
    MODALITY_COLORS = {
        'Small Molecule': '#3498db',
        'Monoclonal Antibody': '#2ecc71',
        'CAR-T': '#e74c3c',
        'Cell & Gene Therapy': '#9b59b6',
        'Viral Vector': '#f39c12',
        'Peptides': '#1abc9c',
        'Oligonucleotides': '#34495e',
        'ADC': '#e67e22',
        'Bispecific Antibody': '#16a085',
        'Vaccine': '#27ae60',
        'Default': '#95a5a6'
    }
    
    MODALITY_ICONS = {
        'Small Molecule': 'fas fa-pills',
        'Monoclonal Antibody': 'fas fa-syringe',
        'CAR-T': 'fas fa-dna',
        'Cell & Gene Therapy': 'fas fa-microscope',
        'Viral Vector': 'fas fa-virus',
        'Peptides': 'fas fa-link',
        'Oligonucleotides': 'fas fa-chain',
        'ADC': 'fas fa-flask',
        'Bispecific Antibody': 'fas fa-project-diagram',
        'Vaccine': 'fas fa-shield-virus',
        'Default': 'fas fa-capsules'
    }
    
    PHASE_ORDER = [
        'Pre-Clinical',
        'Phase I',
        'Phase II',
        'Phase III',
        'Registration',
        'Launched'
    ]
    
    def __init__(self, db_session: Session = None):
        """Initialize the service with a database session."""
        self.db = db_session or db.session
    
    def get_timeline_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point - returns structured data for timeline visualization.
        
        Args:
            config: Configuration dictionary with keys:
                - timelineMode: 'year' | 'phase'
                - yearSegmentPreset: 'individual' | 'grouped' | 'custom'
                - customSegments: List of segment definitions
                - groupingMode: 'modality' | 'therapeutic_area' | 'product_type' | 'none'
                - elementType: 'product' | 'modality'
                - colorBy: 'modality' | 'phase' | 'status'
                - filters: Additional filter criteria
        
        Returns:
            Dictionary with structure:
            {
                "timeline_units": [...],
                "swim_lanes": [...],
                "elements": [...],  (if groupingMode is 'none')
                "metadata": {...}
            }
        """
        products = self._fetch_products(config.get('filters', {}))
        timeline_units = self._build_timeline_units(config, products)
        
        if config.get('groupingMode') == 'none':
            elements = self._prepare_elements(products, config, timeline_units)
            return {
                'timeline_units': timeline_units,
                'elements': elements,
                'swim_lanes': [],
                'metadata': self._build_metadata(config, products, timeline_units)
            }
        else:
            swim_lanes = self._build_swim_lanes(products, config, timeline_units)
            return {
                'timeline_units': timeline_units,
                'swim_lanes': swim_lanes,
                'elements': [],
                'metadata': self._build_metadata(config, products, timeline_units)
            }
    
    def _fetch_products(self, filters: Dict[str, Any]) -> List[Product]:
        """
        Fetches products from database with eager loading of relationships.
        
        Args:
            filters: Dictionary of filter criteria including:
                - therapeutic_area: Filter by therapeutic area
                - current_phase: Filter by development phase
                - modality_id: Filter by modality
                - project_status: Filter by project status
                - include_line_extensions: If False, only returns NMEs (default: True)
                - exclude_discontinued: If True, excludes discontinued products (default: True)
        
        Returns:
            List of Product objects
        """
        query = self.db.query(Product).options(
            joinedload(Product.modality),
            joinedload(Product.parent_nme)
        )
        
        include_line_extensions = filters.get('include_line_extensions', True)
        if not include_line_extensions:
            query = query.filter(Product.is_nme == True)
        
        exclude_discontinued = filters.get('exclude_discontinued', True)
        if exclude_discontinued:
            query = query.filter(
                or_(
                    Product.project_status == None,
                    Product.project_status != 'Discontinued'
                )
            )
        
        if filters.get('therapeutic_area'):
            query = query.filter(Product.therapeutic_area == filters['therapeutic_area'])
        
        if filters.get('current_phase'):
            phases = filters['current_phase']
            if isinstance(phases, list):
                query = query.filter(Product.current_phase.in_(phases))
            else:
                query = query.filter(Product.current_phase == phases)
        
        if filters.get('modality_id'):
            query = query.filter(Product.modality_id == filters['modality_id'])
        
        if filters.get('project_status') and not exclude_discontinued:
            query = query.filter(Product.project_status == filters['project_status'])
        
        query = query.filter(
            or_(
                Product.expected_launch_year.isnot(None),
                Product.current_phase.isnot(None)
            )
        )
        
        return query.order_by(Product.product_code).all()

    def _build_timeline_units(self, config: Dict[str, Any], products: List[Product]) -> List[str]:
        """
        Builds the timeline axis units (years or phases).
        
        Args:
            config: Configuration dictionary
            products: List of products to analyze
        
        Returns:
            List of timeline unit labels
        """
        if config.get('timelineMode') == 'phase':
            return self._build_phase_timeline()
        else:
            return self._build_year_timeline(config, products)
    
    def _build_phase_timeline(self) -> List[str]:
        """Returns the standard phase progression."""
        return self.PHASE_ORDER.copy()
    
    def _build_year_timeline(self, config: Dict[str, Any], products: List[Product]) -> List[str]:
        """
        Builds year-based timeline units.
        
        Args:
            config: Configuration with yearSegmentPreset and customSegments
            products: List of products to determine year range
        
        Returns:
            List of year or year-range labels
        """
        preset = config.get('yearSegmentPreset', 'individual')
        
        if preset == 'custom' and config.get('customSegments'):
            return [seg['label'] for seg in config['customSegments']]
        
        years = [p.expected_launch_year for p in products if p.expected_launch_year]
        
        if not years:
            current_year = datetime.now().year
            years = list(range(current_year, current_year + 10))
        else:
            min_year = min(years)
            max_year = max(years)
            years = list(range(min_year, max_year + 1))
        
        if preset == 'individual':
            return [str(year) for year in years]
        
        elif preset == 'grouped':
            segments = []
            start_year = min(years)
            while start_year <= max(years):
                end_year = min(start_year + 2, max(years))
                if start_year == end_year:
                    segments.append(str(start_year))
                else:
                    segments.append(f"{start_year}-{end_year}")
                start_year = end_year + 1
            return segments
        
        return [str(year) for year in years]
    
    def _build_swim_lanes(self, products: List[Product], config: Dict[str, Any], 
                         timeline_units: List[str]) -> List[Dict[str, Any]]:
        """
        Groups products into swim lanes based on grouping mode.
        
        Args:
            products: List of products
            config: Configuration dictionary
            timeline_units: List of timeline units for positioning
        
        Returns:
            List of swim lane dictionaries
        """
        grouping_mode = config.get('groupingMode', 'modality')
        grouped = self._group_products(products, grouping_mode)
        
        swim_lanes = []
        for group_name, group_products in grouped.items():
            elements = self._prepare_elements(group_products, config, timeline_units)
            
            swim_lanes.append({
                'group_name': group_name or 'Unknown',
                'group_metadata': self._get_group_metadata(group_name, grouping_mode),
                'elements': elements
            })
        
        swim_lanes.sort(key=lambda x: x['group_name'])
        
        return swim_lanes
    
    def _group_products(self, products: List[Product], grouping_mode: str) -> Dict[str, List[Product]]:
        """
        Groups products based on the specified grouping mode.
        
        Args:
            products: List of products
            grouping_mode: How to group products
        
        Returns:
            Dictionary mapping group names to product lists
        """
        grouped = {}
        
        for product in products:
            if grouping_mode == 'modality':
                key = product.modality.modality_name if product.modality else 'Unknown'
            elif grouping_mode == 'therapeutic_area':
                key = product.therapeutic_area or 'Unknown'
            elif grouping_mode == 'product_type':
                key = product.product_type or 'Unknown'
            else:
                key = 'All Products'
            
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(product)
        
        return grouped
    
    def _prepare_elements(self, products: List[Product], config: Dict[str, Any], 
                         timeline_units: List[str]) -> List[Dict[str, Any]]:
        """
        Prepares display elements (products or aggregated modalities).
        
        Args:
            products: List of products
            config: Configuration dictionary
            timeline_units: List of timeline units
        
        Returns:
            List of element dictionaries
        """
        element_type = config.get('elementType', 'product')
        
        if element_type == 'modality':
            return self._aggregate_by_modality(products, config, timeline_units)
        else:
            return self._prepare_product_elements(products, config, timeline_units)
    
    def _prepare_product_elements(self, products: List[Product], config: Dict[str, Any],
                                  timeline_units: List[str]) -> List[Dict[str, Any]]:
        """
        Prepares individual product elements.
        
        Args:
            products: List of products
            config: Configuration dictionary
            timeline_units: List of timeline units
        
        Returns:
            List of product element dictionaries
        """
        elements = []
        
        for product in products:
            position = self._get_product_position(product, config)
            
            if position not in timeline_units:
                continue
            
            visual = self._get_visual_encoding(product, config)
            
            elements.append({
                'id': product.product_id,
                'type': 'product',
                'position': position,
                'data': {
                    'product_id': product.product_id,
                    'product_code': product.product_code,
                    'product_name': product.product_name,
                    'current_phase': product.current_phase,
                    'expected_launch_year': product.expected_launch_year,
                    'project_status': product.project_status,
                    'therapeutic_area': product.therapeutic_area,
                    'modality_name': product.modality.modality_name if product.modality else None,
                    'is_nme': product.is_nme,
                    'is_line_extension': product.is_line_extension,
                    'line_extension_indication': product.line_extension_indication,
                    'launch_sequence': product.launch_sequence,
                    'parent_product_id': product.parent_product_id,
                },
                'visual': visual,
                'count': 1
            })
        
        return elements
    
    def _aggregate_by_modality(self, products: List[Product], config: Dict[str, Any],
                               timeline_units: List[str]) -> List[Dict[str, Any]]:
        """
        Aggregates products by modality for each timeline unit.
        Shows one box per modality per timeline unit.
        
        Args:
            products: List of products
            config: Configuration dictionary
            timeline_units: List of timeline units
        
        Returns:
            List of modality element dictionaries
        """
        aggregated = {}
        
        for product in products:
            position = self._get_product_position(product, config)
            
            if position not in timeline_units:
                continue
            
            modality_name = product.modality.modality_name if product.modality else 'Unknown'
            key = (position, modality_name)
            
            if key not in aggregated:
                aggregated[key] = {
                    'products': [],
                    'modality': product.modality
                }
            
            aggregated[key]['products'].append(product)
        
        elements = []
        for (position, modality_name), data in aggregated.items():
            modality = data['modality']
            product_count = len(data['products'])
            
            visual = {
                'color': self.MODALITY_COLORS.get(modality_name, self.MODALITY_COLORS['Default']),
                'icon': self.MODALITY_ICONS.get(modality_name, self.MODALITY_ICONS['Default']),
                'label': modality_name
            }
            
            elements.append({
                'id': f"modality_{modality.modality_id if modality else 0}_{position}",
                'type': 'modality',
                'position': position,
                'data': {
                    'modality_id': modality.modality_id if modality else None,
                    'modality_name': modality_name,
                    'product_count': product_count,
                    'product_ids': [p.product_id for p in data['products']]
                },
                'visual': visual,
                'count': product_count
            })
        
        return elements
    
    def _get_product_position(self, product: Product, config: Dict[str, Any]) -> str:
        """
        Determines where a product should be positioned on the timeline.
        
        Args:
            product: Product object
            config: Configuration dictionary
        
        Returns:
            Timeline position string
        """
        if config.get('timelineMode') == 'phase':
            return product.current_phase or 'Unknown'
        else:
            year = product.expected_launch_year
            if not year:
                return None
            
            preset = config.get('yearSegmentPreset', 'individual')
            
            if preset == 'individual':
                return str(year)
            
            elif preset == 'grouped':
                return str(year)
            
            elif preset == 'custom':
                segments = config.get('customSegments', [])
                for segment in segments:
                    if segment['yearStart'] <= year <= segment['yearEnd']:
                        return segment['label']
                return None
            
            return str(year)
    
    def _get_visual_encoding(self, product: Product, config: Dict[str, Any]) -> Dict[str, str]:
        """
        Determines visual properties (color, icon) for a product.
        
        Args:
            product: Product object
            config: Configuration dictionary
        
        Returns:
            Dictionary with 'color', 'icon', and 'label' keys
        """
        color_by = config.get('colorBy', 'modality')
        
        if color_by == 'modality' and product.modality:
            modality_name = product.modality.modality_name
            color = self.MODALITY_COLORS.get(modality_name, self.MODALITY_COLORS['Default'])
            icon = self.MODALITY_ICONS.get(modality_name, self.MODALITY_ICONS['Default'])
        else:
            color = self.MODALITY_COLORS['Default']
            icon = self.MODALITY_ICONS['Default']
        
        label = product.product_code or product.product_name
        
        return {
            'color': color,
            'icon': icon,
            'label': label
        }
    
    def _get_group_metadata(self, group_name: str, grouping_mode: str) -> Dict[str, Any]:
        """
        Retrieves metadata about a group.
        
        Args:
            group_name: Name of the group
            grouping_mode: How products are grouped
        
        Returns:
            Dictionary with metadata
        """
        return {
            'grouping_mode': grouping_mode,
            'group_name': group_name
        }
    
    def _build_metadata(self, config: Dict[str, Any], products: List[Product], 
                        timeline_units: List[str]) -> Dict[str, Any]:
        """
        Builds metadata about the timeline including filter information.
        
        Args:
            config: Configuration dictionary
            products: List of products (after filtering)
            timeline_units: List of timeline units
        
        Returns:
            Metadata dictionary with filter summary
        """
        filters = config.get('filters', {})
        
        nme_count = sum(1 for p in products if p.is_nme)
        line_ext_count = sum(1 for p in products if p.is_line_extension)
        discontinued_count = sum(1 for p in products if p.project_status == 'Discontinued')
        active_count = len(products) - discontinued_count
        
        return {
            'total_products': len(products),
            'nme_count': nme_count,
            'line_extension_count': line_ext_count,
            'active_count': active_count,
            'discontinued_count': discontinued_count,
            'timeline_unit_count': len(timeline_units),
            'config': config,
            'active_filters': {
                'include_line_extensions': filters.get('include_line_extensions', True),
                'exclude_discontinued': filters.get('exclude_discontinued', True),
                'therapeutic_area': filters.get('therapeutic_area'),
                'current_phase': filters.get('current_phase'),
                'modality_id': filters.get('modality_id')
            },
            'generated_at': datetime.now().isoformat()
        }


_timeline_service = None

def get_timeline_service(db_session: Session = None) -> PipelineTimelineService:
    """Returns a singleton instance of the timeline service."""
    global _timeline_service
    if _timeline_service is None or db_session is not None:
        _timeline_service = PipelineTimelineService(db_session)
    return _timeline_service