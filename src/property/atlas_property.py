"""Atlas property definitions and mappings."""
from pathlib import Path
from typing import Dict, List, Tuple
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from property import annotation_source


class AtlasProperty:
    """Base class for Atlas properties."""
    
    def __init__(self, annot_source: Path, atlas_name: str):
        self.annotation_source = annot_source
        self.atlas_name = atlas_name


class AtlasBioentityProperty(AtlasProperty):
    """Atlas bioentity property with a bioentity type."""
    
    def __init__(self, annot_source: Path, bioentity_type: annotation_source.Property, atlas_name: str):
        super().__init__(annot_source, atlas_name)
        self.bioentity_type = bioentity_type


class AtlasArrayDesign(AtlasProperty):
    """Atlas array design property."""
    
    def __init__(self, annot_source: Path, atlas_name: str):
        super().__init__(annot_source, atlas_name)


def atlas_bioentity_properties(
    atlas_name: str,
    ensembl_names: List[str],
    annot_source: Path
) -> Dict[AtlasProperty, List[str]]:
    """
    Create atlas bioentity properties for a given annotation source.
    
    Returns:
        Dictionary mapping AtlasProperty to list of corresponding ensembl names
    """
    error, bioentity_types = annotation_source.get_bioentity_type_properties(annot_source)
    
    if error:
        return {}
    
    result = {}
    for bioentity_type in bioentity_types:
        # Filter out the bioentity type value from ensembl names
        filtered_names = [name for name in ensembl_names if name != bioentity_type.value]
        
        # Only include if there are remaining ensembl names
        if filtered_names:
            prop = AtlasBioentityProperty(annot_source, bioentity_type, atlas_name)
            result[prop] = filtered_names
    
    return result


def get_mapping_with_desired_corresponding_properties() -> Dict[AtlasProperty, List[str]]:
    """
    Get mapping of Atlas properties to their desired corresponding Ensembl properties.
    
    Returns:
        Dictionary mapping AtlasProperty to list of Ensembl attribute names
    """
    properties = annotation_source.get_all_properties()
    result = {}
    
    for prop in properties:
        # Skip bioentity type properties
        if prop.is_bioentity_type():
            continue
        
        # Parse comma-separated ensembl names
        ensembl_names = [name.strip() for name in prop.value.split(',')]
        
        # Parse property name
        parts = prop.name.split('.')
        
        if len(parts) == 2:
            if parts[0] == "property":
                # Regular property
                atlas_name = parts[1]
                bioentity_props = atlas_bioentity_properties(
                    atlas_name,
                    ensembl_names,
                    prop.annotation_source
                )
                result.update(bioentity_props)
            
            elif parts[0] == "arrayDesign":
                # Array design
                array_design = parts[1]
                atlas_prop = AtlasArrayDesign(prop.annotation_source, array_design)
                result[atlas_prop] = ensembl_names
    
    return result
