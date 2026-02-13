"""Data transformation for BioMart results."""
from typing import List, Tuple, Optional, Callable
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline.retrieve.tasks import BioMartTask
from property.atlas_property import AtlasBioentityProperty, AtlasArrayDesign
import directories


Result = List[Tuple[str, Optional[str]]]


class Transform:
    """Represents a data transformation."""
    
    def __init__(self, applies_for_task: Callable[[BioMartTask], bool],
                 transform: Callable[[Result], Result]):
        self.applies_for_task = applies_for_task
        self.transform = transform


def lookup_go(value: Optional[str]) -> Optional[str]:
    """Look up canonical GO term for alternative ID."""
    if value is None:
        return None
    
    mapping = directories.alternative_to_canonical_go_term_mapping()
    return mapping.get(value, value)


# GO term transformation
go_transform = Transform(
    applies_for_task=lambda task: (
        isinstance(task.atlas_property, AtlasBioentityProperty) and
        task.atlas_property.atlas_name == "go"
    ),
    transform=lambda result: [
        (k, lookup_go(v)) for k, v in result
    ]
)


# Array design transformation - filter to unique probe sets
def array_design_transform_func(result: Result) -> Result:
    """
    Transform array design results to filter multi-mapping probe sets.
    
    Keep only probe sets that map to exactly one gene.
    """
    # Group by probe set (second column)
    by_probe = {}
    for gene, probe in result:
        if probe not in by_probe:
            by_probe[probe] = []
        by_probe[probe].append(gene)
    
    # Filter to only single-gene mappings or None values
    filtered = []
    for probe, genes in by_probe.items():
        if probe is None:
            # Keep all None mappings
            filtered.extend([(g, None) for g in genes])
        elif len(set(genes)) == 1:
            # Keep single-gene mappings
            filtered.append((genes[0], probe))
    
    return filtered


array_design_transform = Transform(
    applies_for_task=lambda task: isinstance(task.atlas_property, AtlasArrayDesign),
    transform=array_design_transform_func
)


# All transforms to apply
ALL_TRANSFORMS = [go_transform, array_design_transform]


def transform(task: BioMartTask, input_data: Result) -> Result:
    """Apply all applicable transformations to input data."""
    result = input_data
    
    for transform_obj in ALL_TRANSFORMS:
        if transform_obj.applies_for_task(task):
            result = transform_obj.transform(result)
    
    return result
