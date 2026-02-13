"""Path utilities for pipeline outputs."""
from pathlib import Path
from typing import Iterator
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from property.atlas_property import AtlasProperty, AtlasBioentityProperty, AtlasArrayDesign
import directories


def write_result(destination: Path, result: Iterator[str], has_errors: bool = False) -> None:
    """
    Write results to a destination file.
    
    If there are errors, writes to a .failed file.
    Otherwise, writes to a .swp file first, then moves to destination.
    """
    if has_errors:
        failed_path = destination.parent / (destination.name + ".failed")
        with open(failed_path, 'w') as f:
            for line in result:
                f.write(line)
    else:
        swp_path = destination.parent / (destination.name + ".swp")
        with open(swp_path, 'w') as f:
            for line in result:
                f.write(line)
        # Move swap file to destination
        swp_path.rename(destination)


def destination_for(atlas_property: AtlasProperty) -> Path:
    """Get the destination path for an atlas property."""
    return directory_for(atlas_property) / file_name_for(atlas_property)


def file_name_for(atlas_property: AtlasProperty) -> str:
    """Get the filename for an atlas property."""
    if isinstance(atlas_property, AtlasBioentityProperty):
        species = atlas_property.annotation_source.name
        bioentity_type = atlas_property.bioentity_type.name.replace("property.", "")
        atlas_name = atlas_property.atlas_name
        return f"{species}.{bioentity_type}.{atlas_name}.tsv"
    
    elif isinstance(atlas_property, AtlasArrayDesign):
        species = atlas_property.annotation_source.name
        atlas_name = atlas_property.atlas_name
        return f"{species}.{atlas_name}.tsv"
    
    else:
        raise ValueError(f"Unknown atlas property type: {type(atlas_property)}")


def directory_for(atlas_property: AtlasProperty) -> Path:
    """Get the directory for an atlas property."""
    if isinstance(atlas_property, AtlasBioentityProperty):
        # Get the parent directory name (ensembl, wbps, etc.)
        parent_dir = atlas_property.annotation_source.parent.name
        return directories.PATH_BIOENTITY_PROPERTIES / parent_dir
    
    elif isinstance(atlas_property, AtlasArrayDesign):
        return directories.PATH_BIOENTITY_PROPERTIES / "array_designs" / "current"
    
    else:
        raise ValueError(f"Unknown atlas property type: {type(atlas_property)}")
