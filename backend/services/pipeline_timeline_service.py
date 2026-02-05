"""
Pipeline Timeline Service

Provides data aggregation and transformation for the pipeline timeline visualization.
Supports flexible configurations for timeline axes, groupings, and display modes.

Updated to use Project model instead of Product model.
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..models import Project, DrugSubstance, Modality, db


class PipelineTimelineService:
    """Service for generating pipeline timeline data based on configuration."""

    # Colors for molecule types / modalities (includes common alternative spellings)
    MODALITY_COLORS = {
        # Small molecules
        'Small Molecule': '#3498db',
        'Small molecule': '#3498db',
        'small molecule': '#3498db',
        'NCE': '#3498db',
        # Monoclonal antibodies
        'Monoclonal Antibody': '#2ecc71',
        'mAb': '#2ecc71',
        'MAb': '#2ecc71',
        'Antibody': '#2ecc71',
        # CAR-T
        'CAR-T': '#e74c3c',
        'CAR-T cell': '#e74c3c',
        # Cell & Gene Therapy
        'Cell & Gene Therapy': '#9b59b6',
        'Gene Therapy': '#9b59b6',
        'Cell Therapy': '#9b59b6',
        # Viral Vector
        'Viral Vector': '#f39c12',
        'AAV': '#f39c12',
        # Peptides
        'Peptides': '#1abc9c',
        'Peptide': '#1abc9c',
        # Oligonucleotides
        'Oligonucleotides': '#34495e',
        'Oligonucleotide': '#34495e',
        'ASO': '#34495e',
        'siRNA': '#34495e',
        # ADC
        'ADC': '#e67e22',
        'Antibody-Drug Conjugate': '#e67e22',
        # Bispecific
        'Bispecific Antibody': '#16a085',
        'Bispecific': '#16a085',
        # Vaccine
        'Vaccine': '#27ae60',
        # Default
        'Default': '#95a5a6'
    }

    MODALITY_ICONS = {
        # Small molecules
        'Small Molecule': 'fas fa-pills',
        'Small molecule': 'fas fa-pills',
        'small molecule': 'fas fa-pills',
        'NCE': 'fas fa-pills',
        # Monoclonal antibodies
        'Monoclonal Antibody': 'fas fa-syringe',
        'mAb': 'fas fa-syringe',
        'MAb': 'fas fa-syringe',
        'Antibody': 'fas fa-syringe',
        # CAR-T
        'CAR-T': 'fas fa-dna',
        'CAR-T cell': 'fas fa-dna',
        # Cell & Gene Therapy
        'Cell & Gene Therapy': 'fas fa-microscope',
        'Gene Therapy': 'fas fa-microscope',
        'Cell Therapy': 'fas fa-microscope',
        # Viral Vector
        'Viral Vector': 'fas fa-virus',
        'AAV': 'fas fa-virus',
        # Peptides
        'Peptides': 'fas fa-link',
        'Peptide': 'fas fa-link',
        # Oligonucleotides
        'Oligonucleotides': 'fas fa-chain',
        'Oligonucleotide': 'fas fa-chain',
        'ASO': 'fas fa-chain',
        'siRNA': 'fas fa-chain',
        # ADC
        'ADC': 'fas fa-flask',
        'Antibody-Drug Conjugate': 'fas fa-flask',
        # Bispecific
        'Bispecific Antibody': 'fas fa-project-diagram',
        'Bispecific': 'fas fa-project-diagram',
        # Vaccine
        'Vaccine': 'fas fa-shield-virus',
        # Default
        'Default': 'fas fa-capsules'
    }

    # Project types that count as "line extensions"
    LINE_EXTENSION_TYPES = ['NI', 'PMO', 'PED']

    def __init__(self, db_session: Session = None):
        """Initialize the service with a database session."""
        self.db = db_session or db.session

    def _get_project_modality_name(self, project: Project) -> Optional[str]:
        """Get modality name from project's first drug substance.

        Uses molecule_type field as the primary source (e.g., 'Small molecule', 'mAb').
        Falls back to modality relationship if molecule_type is not set.
        """
        if project.drug_substances:
            ds = project.drug_substances[0]
            # Primary: use molecule_type field
            if ds.molecule_type:
                return ds.molecule_type
            # Fallback: use modality relationship
            if hasattr(ds, 'modality') and ds.modality:
                return ds.modality.modality_name
        return None

    def _get_launch_year(self, project: Project) -> Optional[int]:
        """Extract year from project's launch date."""
        if project.launch:
            return project.launch.year
        return None

    def _is_nme(self, project: Project) -> bool:
        """Check if project is a New Molecular Entity."""
        return project.project_type == 'NME'

    def _is_line_extension(self, project: Project) -> bool:
        """Check if project is a line extension (NI, PMO, PED)."""
        return project.project_type in self.LINE_EXTENSION_TYPES

    def get_timeline_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point - returns structured data for timeline visualization.

        Args:
            config: Configuration dictionary with keys:
                - timelineMode: 'year' | 'phase'
                - yearSegmentPreset: 'individual' | 'grouped' | 'custom'
                - customSegments: List of segment definitions
                - groupingMode: 'modality' | 'therapeutic_area' | 'project_type' | 'none'
                - elementType: 'project' | 'modality'
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
        projects = self._fetch_projects(config.get('filters', {}))
        timeline_units = self._build_timeline_units(config, projects)

        if config.get('groupingMode') == 'none':
            elements = self._prepare_elements(projects, config, timeline_units)
            return {
                'timeline_units': timeline_units,
                'elements': elements,
                'swim_lanes': [],
                'metadata': self._build_metadata(config, projects, timeline_units)
            }
        else:
            swim_lanes = self._build_swim_lanes(projects, config, timeline_units)
            return {
                'timeline_units': timeline_units,
                'swim_lanes': swim_lanes,
                'elements': [],
                'metadata': self._build_metadata(config, projects, timeline_units)
            }

    def _fetch_projects(self, filters: Dict[str, Any]) -> List[Project]:
        """
        Fetches projects from database with eager loading of relationships.

        Args:
            filters: Dictionary of filter criteria including:
                - indication: Filter by indication
                - modality_id: Filter by modality (via drug_substances)
                - include_line_extensions: If False, only returns NMEs (default: True)
                - exclude_discontinued: If True, excludes discontinued projects (default: True)

        Returns:
            List of Project objects
        """
        query = self.db.query(Project).options(
            joinedload(Project.drug_substances).joinedload(DrugSubstance.modality)
        )

        # Filter: Only NMEs (exclude line extensions)
        include_line_extensions = filters.get('include_line_extensions', True)
        if not include_line_extensions:
            query = query.filter(Project.project_type == 'NME')

        # Filter: Exclude discontinued projects
        exclude_discontinued = filters.get('exclude_discontinued', True)
        if exclude_discontinued:
            query = query.filter(
                or_(
                    Project.status == None,
                    Project.status != 'discontinued'
                )
            )

        # Filter: By indication (therapeutic area equivalent)
        if filters.get('indication'):
            query = query.filter(Project.indication == filters['indication'])

        # Filter: By project type
        if filters.get('project_type'):
            types = filters['project_type']
            if isinstance(types, list):
                query = query.filter(Project.project_type.in_(types))
            else:
                query = query.filter(Project.project_type == types)

        # Only include projects with a launch date
        query = query.filter(Project.launch.isnot(None))

        return query.order_by(Project.name).all()

    def _build_timeline_units(self, config: Dict[str, Any], projects: List[Project]) -> List[str]:
        """
        Builds the timeline axis units (years).

        Args:
            config: Configuration dictionary
            projects: List of projects to analyze

        Returns:
            List of timeline unit labels
        """
        return self._build_year_timeline(config, projects)

    def _build_year_timeline(self, config: Dict[str, Any], projects: List[Project]) -> List[str]:
        """
        Builds year-based timeline units.

        Args:
            config: Configuration with yearSegmentPreset and customSegments
            projects: List of projects to determine year range

        Returns:
            List of year or year-range labels
        """
        preset = config.get('yearSegmentPreset', 'individual')

        if preset == 'custom' and config.get('customSegments'):
            return [seg['label'] for seg in config['customSegments']]

        years = [self._get_launch_year(p) for p in projects]
        years = [y for y in years if y is not None]

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

    def _build_swim_lanes(self, projects: List[Project], config: Dict[str, Any],
                         timeline_units: List[str]) -> List[Dict[str, Any]]:
        """
        Groups projects into swim lanes based on grouping mode.

        Args:
            projects: List of projects
            config: Configuration dictionary
            timeline_units: List of timeline units for positioning

        Returns:
            List of swim lane dictionaries
        """
        grouping_mode = config.get('groupingMode', 'modality')
        grouped = self._group_projects(projects, grouping_mode)

        swim_lanes = []
        for group_name, group_projects in grouped.items():
            elements = self._prepare_elements(group_projects, config, timeline_units)

            swim_lanes.append({
                'group_name': group_name or 'Unknown',
                'group_metadata': self._get_group_metadata(group_name, grouping_mode),
                'elements': elements
            })

        swim_lanes.sort(key=lambda x: x['group_name'])

        return swim_lanes

    def _group_projects(self, projects: List[Project], grouping_mode: str) -> Dict[str, List[Project]]:
        """
        Groups projects based on the specified grouping mode.

        Args:
            projects: List of projects
            grouping_mode: How to group projects

        Returns:
            Dictionary mapping group names to project lists
        """
        grouped = {}

        for project in projects:
            if grouping_mode == 'modality':
                key = self._get_project_modality_name(project) or 'Unknown'
            elif grouping_mode == 'therapeutic_area':
                key = project.indication or 'Unknown'
            elif grouping_mode == 'project_type':
                key = project.project_type or 'Unknown'
            else:
                key = 'All Projects'

            if key not in grouped:
                grouped[key] = []
            grouped[key].append(project)

        return grouped

    def _prepare_elements(self, projects: List[Project], config: Dict[str, Any],
                         timeline_units: List[str]) -> List[Dict[str, Any]]:
        """
        Prepares display elements (projects or aggregated modalities).

        Args:
            projects: List of projects
            config: Configuration dictionary
            timeline_units: List of timeline units

        Returns:
            List of element dictionaries
        """
        element_type = config.get('elementType', 'project')

        if element_type == 'modality':
            return self._aggregate_by_modality(projects, config, timeline_units)
        else:
            return self._prepare_project_elements(projects, config, timeline_units)

    def _prepare_project_elements(self, projects: List[Project], config: Dict[str, Any],
                                  timeline_units: List[str]) -> List[Dict[str, Any]]:
        """
        Prepares individual project elements.

        Args:
            projects: List of projects
            config: Configuration dictionary
            timeline_units: List of timeline units

        Returns:
            List of project element dictionaries
        """
        elements = []

        for project in projects:
            position = self._get_project_position(project, config)

            if position not in timeline_units:
                continue

            visual = self._get_visual_encoding(project, config)
            modality_name = self._get_project_modality_name(project)

            elements.append({
                'id': project.id,
                'type': 'project',
                'position': position,
                'data': {
                    'project_id': project.id,
                    'project_name': project.name,
                    'indication': project.indication,
                    'project_type': project.project_type,
                    'expected_launch_year': self._get_launch_year(project),
                    'status': project.status,
                    'modality_name': modality_name,
                    'is_nme': self._is_nme(project),
                    'is_line_extension': self._is_line_extension(project),
                },
                'visual': visual,
                'count': 1
            })

        return elements

    def _aggregate_by_modality(self, projects: List[Project], config: Dict[str, Any],
                               timeline_units: List[str]) -> List[Dict[str, Any]]:
        """
        Aggregates projects by modality for each timeline unit.
        Shows one box per modality per timeline unit.

        Args:
            projects: List of projects
            config: Configuration dictionary
            timeline_units: List of timeline units

        Returns:
            List of modality element dictionaries
        """
        aggregated = {}

        for project in projects:
            position = self._get_project_position(project, config)

            if position not in timeline_units:
                continue

            modality_name = self._get_project_modality_name(project) or 'Unknown'
            key = (position, modality_name)

            if key not in aggregated:
                aggregated[key] = {
                    'projects': [],
                    'modality_name': modality_name
                }

            aggregated[key]['projects'].append(project)

        elements = []
        for (position, modality_name), data in aggregated.items():
            project_count = len(data['projects'])

            visual = {
                'color': self.MODALITY_COLORS.get(modality_name, self.MODALITY_COLORS['Default']),
                'icon': self.MODALITY_ICONS.get(modality_name, self.MODALITY_ICONS['Default']),
                'label': modality_name
            }

            elements.append({
                'id': f"modality_{modality_name}_{position}",
                'type': 'modality',
                'position': position,
                'data': {
                    'modality_name': modality_name,
                    'project_count': project_count,
                    'project_ids': [p.id for p in data['projects']]
                },
                'visual': visual,
                'count': project_count
            })

        return elements

    def _get_project_position(self, project: Project, config: Dict[str, Any]) -> str:
        """
        Determines where a project should be positioned on the timeline.

        Args:
            project: Project object
            config: Configuration dictionary

        Returns:
            Timeline position string
        """
        year = self._get_launch_year(project)
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

    def _get_visual_encoding(self, project: Project, config: Dict[str, Any]) -> Dict[str, str]:
        """
        Determines visual properties (color, icon) for a project.

        Args:
            project: Project object
            config: Configuration dictionary

        Returns:
            Dictionary with 'color', 'icon', and 'label' keys
        """
        color_by = config.get('colorBy', 'modality')
        modality_name = self._get_project_modality_name(project)

        if color_by == 'modality' and modality_name:
            color = self.MODALITY_COLORS.get(modality_name, self.MODALITY_COLORS['Default'])
            icon = self.MODALITY_ICONS.get(modality_name, self.MODALITY_ICONS['Default'])
        else:
            color = self.MODALITY_COLORS['Default']
            icon = self.MODALITY_ICONS['Default']

        label = project.name

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
            grouping_mode: How projects are grouped

        Returns:
            Dictionary with metadata
        """
        return {
            'grouping_mode': grouping_mode,
            'group_name': group_name
        }

    def _build_metadata(self, config: Dict[str, Any], projects: List[Project],
                        timeline_units: List[str]) -> Dict[str, Any]:
        """
        Builds metadata about the timeline including filter information.

        Args:
            config: Configuration dictionary
            projects: List of projects (after filtering)
            timeline_units: List of timeline units

        Returns:
            Metadata dictionary with filter summary
        """
        filters = config.get('filters', {})

        nme_count = sum(1 for p in projects if self._is_nme(p))
        line_ext_count = sum(1 for p in projects if self._is_line_extension(p))
        discontinued_count = sum(1 for p in projects if p.status == 'discontinued')
        active_count = len(projects) - discontinued_count

        return {
            'total_projects': len(projects),
            'nme_count': nme_count,
            'line_extension_count': line_ext_count,
            'active_count': active_count,
            'discontinued_count': discontinued_count,
            'timeline_unit_count': len(timeline_units),
            'config': config,
            'active_filters': {
                'include_line_extensions': filters.get('include_line_extensions', True),
                'exclude_discontinued': filters.get('exclude_discontinued', True),
                'indication': filters.get('indication'),
                'project_type': filters.get('project_type'),
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
