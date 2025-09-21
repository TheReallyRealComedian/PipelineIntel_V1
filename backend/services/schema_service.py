# backend/services/schema_service.py
import os
import tempfile
from eralchemy2 import render_er
from ..db import db
import base64

def generate_schema_diagram(format='png'):
    """
    Generates a database schema diagram and returns it as base64 encoded data.
    
    Args:
        format: Output format ('png', 'pdf', 'svg')
    
    Returns:
        tuple: (base64_encoded_data, mime_type)
    """
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=f'.{format}', delete=False) as tmp:
            tmp_path = tmp.name
        
        # Generate diagram from SQLAlchemy metadata
        render_er(db.metadata, tmp_path)
        
        # Read and encode the file
        with open(tmp_path, 'rb') as f:
            diagram_data = f.read()
            encoded = base64.b64encode(diagram_data).decode('utf-8')
        
        # Clean up
        os.unlink(tmp_path)
        
        # Determine MIME type
        mime_types = {
            'png': 'image/png',
            'pdf': 'application/pdf',
            'svg': 'image/svg+xml'
        }
        
        return encoded, mime_types.get(format, 'image/png')
        
    except Exception as e:
        print(f"Error generating schema diagram: {e}")
        return None, None

def get_schema_statistics():
    """
    Returns basic statistics about the database schema.
    """
    try:
        stats = {
            'total_tables': len(db.metadata.tables),
            'tables': []
        }
        
        for table_name, table in db.metadata.tables.items():
            if table_name != 'flask_sessions':  # Exclude system tables
                stats['tables'].append({
                    'name': table_name,
                    'columns': len(table.columns),
                    'foreign_keys': len(table.foreign_keys),
                    'primary_keys': len(table.primary_key.columns)
                })
        
        stats['tables'].sort(key=lambda x: x['name'])
        return stats
        
    except Exception as e:
        print(f"Error getting schema statistics: {e}")
        return None