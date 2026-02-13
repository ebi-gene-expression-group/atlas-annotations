"""
Check the annotations prescribe the retrieval of data we need.
- All array designs specified in processing directories are also in the annotations
"""
from pathlib import Path
from typing import List, Tuple, Set, Optional
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import directories
from experiment import experiment_directory
from property import annotation_source


def get_array_designs_backfilled() -> List[str]:
    """Get array designs from backfill directory."""
    backfill_dir = directories.PATH_BIOENTITY_PROPERTIES / "array_designs" / "backfill"
    
    if not backfill_dir.exists():
        return []
    
    array_designs = []
    for file_path in backfill_dir.iterdir():
        if file_path.is_file():
            parts = file_path.name.split('.')
            if len(parts) >= 3 and parts[-1] == 'tsv':
                # Extract array design accession (second part)
                array_designs.append(parts[1])
    
    return array_designs


def get_array_designs_missing_from_annotation_sources() -> List[str]:
    """Get array designs that are missing from annotation sources."""
    # Get array designs present in annotation sources
    array_designs_present: Set[str] = set()
    
    properties = annotation_source.get_all_properties()
    for prop in properties:
        accession = prop.get_as_array_design_accession()
        if accession:
            array_designs_present.add(accession)
    
    # Add backfilled array designs
    array_designs_present.update(get_array_designs_backfilled())
    
    # Get all array designs from experiments
    all_array_designs = experiment_directory.get_all_array_designs()
    
    # Find missing array designs
    errors = []
    for array_designs_tuple, experiment_accessions in all_array_designs.items():
        array_designs_set = set(array_designs_tuple)
        missing = array_designs_set - array_designs_present
        
        if missing:
            missing_str = ', '.join(missing)
            experiments_str = ', '.join(experiment_accessions)
            errors.append(
                f"{missing_str} missing from annotations but required for experiments {experiments_str}"
            )
    
    return errors


def get_annotations_required_for_redecoration_missing_per_species() -> List[str]:
    """Get required annotations that are missing per species."""
    # Required properties for experiment decoration
    required_properties = {"property.go", "property.interpro", "property.symbol"}
    
    # Group properties by species
    species_properties = {}
    properties = annotation_source.get_all_properties()
    
    for prop in properties:
        species_name = prop.annotation_source.name
        if species_name not in species_properties:
            species_properties[species_name] = set()
        species_properties[species_name].add(prop.name)
    
    # Find missing properties per species
    errors = []
    for species, props in species_properties.items():
        missing = required_properties - props
        if missing:
            missing_str = ', '.join(missing)
            errors.append(
                f"{missing_str} missing for species {species} but required for experiment decoration!"
            )
    
    return errors


def main() -> Tuple[Optional[str], Optional[str]]:
    """
    Validate annotation sources.
    
    Returns:
        (None, "success") on success
        (error_message, None) on failure
    """
    errors = []
    
    errors.extend(get_array_designs_missing_from_annotation_sources())
    errors.extend(get_annotations_required_for_redecoration_missing_per_species())
    
    if not errors:
        return (None, "Validation passed")
    else:
        return ('\n'.join(errors), None)


if __name__ == "__main__":
    error, success = main()
    if error:
        print(error, file=sys.stderr)
        sys.exit(1)
    else:
        print(success)
        sys.exit(0)
