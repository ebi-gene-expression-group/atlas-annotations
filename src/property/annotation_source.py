"""Annotation source property handling."""
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

import directories


class Property:
    """Represents a property from an annotation source."""
    
    def __init__(self, annotation_source: Path, name: str, value: str):
        self.annotation_source = annotation_source
        self.name = name
        self.value = value
    
    def is_bioentity_type(self) -> bool:
        """Check if this property is a bioentity type property."""
        result = get_bioentity_type_properties(self.annotation_source)
        if isinstance(result, tuple) and result[0] is None:
            _, props = result
            return self.name in [p.name for p in props]
        return False
    
    def get_as_array_design_accession(self) -> Optional[str]:
        """Extract array design accession if this is an array design property."""
        if self.name.startswith("arrayDesign."):
            return self.name.replace("arrayDesign.", "")
        return None
    
    @staticmethod
    def read_from_annotation_source(annotation_source: Path) -> List['Property']:
        """Read all properties from an annotation source file."""
        properties = []
        
        if not annotation_source.exists():
            return properties
        
        with open(annotation_source, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Skip comments
                if line.startswith('#'):
                    continue
                
                # Parse key=value
                if '=' not in line:
                    continue
                
                parts = line.split('=', 1)
                if len(parts) != 2:
                    continue
                
                name = parts[0].strip()
                value = parts[1].strip()
                
                # Skip empty values or names
                if not name or not value:
                    continue
                
                properties.append(Property(annotation_source, name, value))
        
        return properties


def get_bioentity_type_properties(annotation_source: Path) -> Tuple[Optional[str], Optional[List[Property]]]:
    """
    Get bioentity type properties for an annotation source.
    
    Returns:
        (None, properties) on success
        (error_message, None) on failure
    """
    # Get the 'types' property value
    error, value = get_value(annotation_source, "types")
    if error:
        return (error, None)
    
    # Parse comma-separated types and prefix with "property."
    bioentity_property_names = [f"property.{v.strip()}" for v in value.split(',')]
    
    # Read all properties from the source
    all_props = Property.read_from_annotation_source(annotation_source)
    
    # Filter to only bioentity type properties
    matching_props = [p for p in all_props if p.name in bioentity_property_names]
    
    if len(matching_props) == len(bioentity_property_names):
        return (None, matching_props)
    else:
        found_names = [p.name for p in matching_props]
        return (f"Required: {bioentity_property_names} but found: {found_names}", None)


# Global cache of properties
_properties_cache: Optional[List[Property]] = None


def get_all_properties() -> List[Property]:
    """Get all properties from all annotation sources."""
    global _properties_cache
    if _properties_cache is None:
        _properties_cache = []
        for source in directories.annotation_sources():
            _properties_cache.extend(Property.read_from_annotation_source(source))
    return _properties_cache


def get_optional_value(annotation_source: Path, property_name: str) -> Optional[str]:
    """Get an optional property value."""
    properties = get_all_properties()
    for prop in properties:
        if prop.annotation_source == annotation_source and prop.name == property_name:
            return prop.value
    return None


def get_value(annotation_source: Path, property_name: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Get a required property value.
    
    Returns:
        (None, value) on success
        (error_message, None) on failure
    """
    value = get_optional_value(annotation_source, property_name)
    if value is not None:
        return (None, value)
    else:
        return (f"Property {property_name} missing for annotation source {annotation_source}", None)


def get_values(annotation_source: Path, property_names: List[str]) -> Tuple[Optional[str], Optional[List[str]]]:
    """
    Get multiple required property values.
    
    Returns:
        (None, [values]) on success
        (error_message, None) on failure
    """
    properties = get_all_properties()
    
    # Build a map of property names to values for this annotation source
    prop_map = {}
    for prop in properties:
        if prop.annotation_source == annotation_source and prop.name in property_names:
            prop_map[prop.name] = prop.value
    
    # Check if all required properties are present
    if set(prop_map.keys()) == set(property_names):
        # Return values in the same order as requested
        return (None, [prop_map[name] for name in property_names])
    else:
        missing = set(property_names) - set(prop_map.keys())
        return (f"Properties {', '.join(missing)} missing for annotation source {annotation_source}", None)
