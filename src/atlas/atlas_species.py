#!/usr/bin/env python3
"""Generate Atlas species JSON configuration."""
import json
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

import directories
from property import annotation_source
from util import combinators


class AtlasSpecies:
    """Represents an Atlas species configuration."""
    
    def __init__(self, species: str, default_query_factor_type: str, kingdom: str,
                 resources: List[Tuple[str, List[Tuple[str, str]]]]):
        self.species = species
        self.default_query_factor_type = default_query_factor_type
        self.kingdom = kingdom
        self.resources = resources
    
    def to_json(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        resources_list = []
        for r_type, r_values in self.resources:
            for name, url in r_values:
                resources_list.append({
                    "type": r_type,
                    "name": name,
                    "url": url
                })
        
        return {
            "name": self.species,
            "defaultQueryFactorType": self.default_query_factor_type,
            "kingdom": self.kingdom,
            "resources": resources_list
        }


class AtlasSpeciesFactory:
    """Factory for creating AtlasSpecies instances."""
    
    DEFAULT_QUERY_FACTOR_TYPES_MAP = {
        "parasite": "DEVELOPMENTAL_STAGE"
    }
    
    KINGDOM_MAP = {
        "ensembl": "animals",
        "metazoa": "animals",
        "fungi": "fungi",
        "parasite": "animals",
        "plants": "plants",
        "protists": "protists"
    }
    
    RESOURCES_MAP = {
        "genome_browser": {
            "ensembl": [("Ensembl", "https://www.ensembl.org/")],
            "metazoa": [("Ensembl Genomes", "https://metazoa.ensembl.org/")],
            "fungi": [("Ensembl Genomes", "https://fungi.ensembl.org/")],
            "parasite": [("Wormbase ParaSite", "https://parasite.wormbase.org/")],
            "plants": [
                ("Gramene", "http://ensembl.gramene.org/"),
                ("Ensembl Genomes", "https://plants.ensembl.org/")
            ],
            "protists": [("Ensembl Genomes", "https://protists.ensembl.org/")]
        }
    }
    
    @staticmethod
    def create(annot_source: Path) -> Tuple[Optional[str], Optional[AtlasSpecies]]:
        """
        Create an AtlasSpecies from an annotation source.
        
        Returns:
            (None, AtlasSpecies) on success
            (error_message, None) on failure
        """
        error, values = annotation_source.get_values(annot_source, ["databaseName", "mySqlDbName"])
        
        if error:
            return (error, None)
        
        database_name, mysql_db_name = values
        
        species_name = species_name_from_source(annot_source)
        default_query_factor_type = AtlasSpeciesFactory.DEFAULT_QUERY_FACTOR_TYPES_MAP.get(
            database_name, "ORGANISM_PART"
        )
        kingdom = AtlasSpeciesFactory.KINGDOM_MAP.get(database_name, "animals")
        
        # Build resources
        resources = []
        for key, values_map in AtlasSpeciesFactory.RESOURCES_MAP.items():
            if database_name in values_map:
                resource_list = []
                for name, url in values_map[database_name]:
                    # Capitalize the mysql db name and append to URL
                    full_url = url + mysql_db_name.capitalize()
                    resource_list.append((name, full_url))
                resources.append((key, resource_list))
        
        atlas_species = AtlasSpecies(
            species_name,
            default_query_factor_type,
            kingdom,
            resources
        )
        
        return (None, atlas_species)


def species_name_from_source(annot_source: Path) -> str:
    """Get species name from annotation source path."""
    return annot_source.name.capitalize()


def atlas_species_from_all_annotation_sources() -> Tuple[Optional[List[str]], Optional[List[AtlasSpecies]]]:
    """
    Create AtlasSpecies for all annotation sources.
    
    Returns:
        (None, [AtlasSpecies]) on success
        ([errors], None) on failure
    """
    # Group annotation sources by species name
    sources_by_species: Dict[str, List[Path]] = {}
    for source in directories.annotation_sources():
        species = species_name_from_source(source)
        if species not in sources_by_species:
            sources_by_species[species] = []
        sources_by_species[species].append(source)
    
    # Create AtlasSpecies for each species (using the first source for each)
    results = []
    for species_name, sources in sources_by_species.items():
        # Try each source for this species until one succeeds
        species_results = [AtlasSpeciesFactory.create(source) for source in sources]
        error, success = combinators.combine_any(species_results)
        
        if error and not success:
            # All failed for this species
            results.append((error, None))
        else:
            # At least one succeeded - use the first success
            results.append((None, success[0]))
    
    # Combine all results
    error, species_list = combinators.combine(results)
    
    if error:
        return (error, None)
    else:
        return (None, species_list)


def dump() -> None:
    """Main entry point - dump species JSON to stdout."""
    error, species_list = atlas_species_from_all_annotation_sources()
    
    if error:
        print(error, file=sys.stderr)
        sys.exit(1)
    else:
        # Sort by species name
        sorted_species = sorted(species_list, key=lambda s: s.species)
        
        # Convert to JSON
        json_list = [s.to_json() for s in sorted_species]
        
        # Print as formatted JSON array
        print(json.dumps(json_list, indent=2))


if __name__ == "__main__":
    dump()
