"""Task definitions for BioMart retrieval."""
from pathlib import Path
from typing import List, Tuple, Dict
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from property import annotation_source, atlas_property
from property.atlas_property import AtlasProperty, AtlasBioentityProperty, AtlasArrayDesign
from pipeline import paths


class BioMartTask:
    """Represents a BioMart retrieval task."""
    
    def __init__(self, atlas_prop: AtlasProperty, queries: List[Tuple[Dict[str, str], List[str]]],
                 destination: Path):
        self.atlas_property = atlas_prop
        self.queries = queries
        self.destination = destination
    
    @property
    def annotation_source(self) -> Path:
        """Get the annotation source for this task."""
        return self.atlas_property.annotation_source
    
    def seems_done(self) -> bool:
        """Check if the task seems to be already completed."""
        return self.destination.exists()
    
    def ensembl_attributes_involved(self) -> set:
        """Get all Ensembl attributes involved in this task."""
        attrs = set()
        for _, attributes in self.queries:
            attrs.update(attributes)
        return attrs
    
    def __str__(self) -> str:
        return f"BioMart task for {self.annotation_source}: {len(self.queries)} queries, destination: {self.destination}"


def ensembl_name_of_reference_column(atlas_prop: AtlasProperty) -> str:
    """Get the Ensembl name of the reference column for an Atlas property."""
    if isinstance(atlas_prop, AtlasBioentityProperty):
        return atlas_prop.bioentity_type.value
    elif isinstance(atlas_prop, AtlasArrayDesign):
        return "ensembl_gene_id"
    else:
        raise ValueError(f"Unknown atlas property type: {type(atlas_prop)}")


def queries_for_atlas_property(atlas_prop: AtlasProperty,
                                desired_corresponding_properties: List[str]) -> List[Tuple[Dict[str, str], List[str]]]:
    """
    Generate queries for an Atlas property.
    
    Returns:
        List of (filters, attributes) tuples
    """
    # Get chromosome shards if available
    error, chromosome_names = annotation_source.get_value(atlas_prop.annotation_source, "chromosomeName")
    
    if error:
        # No chromosomes - single query with no filters
        shards = [{}]
    else:
        # Split by chromosomes
        shards = [{"chromosome_name": chrom} for chrom in chromosome_names.split(',')]
    
    # Generate queries for each ensembl property and each shard
    queries = []
    for ensembl_name in desired_corresponding_properties:
        attributes = [
            ensembl_name_of_reference_column(atlas_prop),
            ensembl_name
        ]
        
        for shard_filters in shards:
            queries.append((shard_filters, attributes))
    
    return queries


def retrieval_plan_for_atlas_property(atlas_prop: AtlasProperty,
                                      desired_corresponding_properties: List[str]) -> BioMartTask:
    """Create a BioMart task for an Atlas property."""
    queries = queries_for_atlas_property(atlas_prop, desired_corresponding_properties)
    destination = paths.destination_for(atlas_prop)
    
    return BioMartTask(atlas_prop, queries, destination)


def all_tasks() -> List[BioMartTask]:
    """Get all BioMart tasks for all Atlas properties."""
    mapping = atlas_property.get_mapping_with_desired_corresponding_properties()
    
    tasks = []
    for atlas_prop, desired_properties in mapping.items():
        task = retrieval_plan_for_atlas_property(atlas_prop, desired_properties)
        tasks.append(task)
    
    return tasks
