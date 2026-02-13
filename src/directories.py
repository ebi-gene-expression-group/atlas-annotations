"""Directory and path configuration for atlas-annotations."""
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional


# Get project root - the directory where annsrcs exists
PROJECT_ROOT = Path.cwd()

if not (PROJECT_ROOT / "annsrcs").is_dir():
    raise RuntimeError(f"Annotations directory not found, possibly called from wrong place: {PROJECT_ROOT / 'annsrcs'}")


def get_path_bioentity_properties() -> Path:
    """Get the PATH_BIOENTITY_PROPERTIES directory."""
    path_str = os.environ.get("PATH_BIOENTITY_PROPERTIES")
    if not path_str:
        raise RuntimeError("export $PATH_BIOENTITY_PROPERTIES as an environment variable")
    
    path = Path(path_str)
    if not path.is_dir():
        raise RuntimeError(f"PATH_BIOENTITY_PROPERTIES is not a valid directory: {path}")
    
    return path


PATH_BIOENTITY_PROPERTIES = get_path_bioentity_properties()


def get_alternative_to_canonical_go_term_mapping() -> Dict[str, str]:
    """Load GO alternative ID to canonical ID mapping."""
    mapping = {}
    mapping_file = PATH_BIOENTITY_PROPERTIES / "go" / "go.alternativeID2CanonicalID.tsv"
    
    if not mapping_file.exists():
        return mapping
    
    with open(mapping_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split('\t')
            if len(parts) == 2:
                mapping[parts[0]] = parts[1]
    
    return mapping


# Lazy load the mapping
_alternative_to_canonical_go_term_mapping: Optional[Dict[str, str]] = None


def alternative_to_canonical_go_term_mapping() -> Dict[str, str]:
    """Get the GO alternative to canonical mapping (lazy loaded)."""
    global _alternative_to_canonical_go_term_mapping
    if _alternative_to_canonical_go_term_mapping is None:
        _alternative_to_canonical_go_term_mapping = get_alternative_to_canonical_go_term_mapping()
    return _alternative_to_canonical_go_term_mapping


def get_annotation_sources() -> List[Path]:
    """
    Get annotation sources paths.
    
    Default paths for annotation sources, within the project.
    If you wish to override them, set the env var ANNOTATION_SOURCES
    to a list of paths separated by colon (:).
    """
    annsrcs_path = PROJECT_ROOT / "annsrcs" / "ensembl"
    
    annotation_sources_env = os.environ.get("ANNOTATION_SOURCES")
    
    if annotation_sources_env:
        # Parse colon-separated paths
        paths = []
        for path_str in annotation_sources_env.split(':'):
            path = Path(path_str)
            if path.exists() and path.is_dir():
                # List all items in the directory
                paths.extend([p for p in path.iterdir()])
        
        if paths:
            return paths
    
    # Default: list all items in annsrcs/ensembl
    if annsrcs_path.exists() and annsrcs_path.is_dir():
        return list(annsrcs_path.iterdir())
    
    return []


ANNOTATION_SOURCES = get_annotation_sources()


def annotation_sources() -> List[Path]:
    """Get annotation source files (species files matching pattern [a-z]+_[a-z]+)."""
    sources = []
    for path in ANNOTATION_SOURCES:
        if path.is_file():
            # Check if filename matches species pattern
            name = path.name
            if '_' in name:
                parts = name.split('_')
                if len(parts) == 2 and parts[0].islower() and parts[1].islower():
                    sources.append(path)
    return sources


def get_experiment_sources() -> List[Path]:
    """
    Get experiment source directories.
    
    EXPERIMENT_SOURCES should be defined as an environment variable as a list of
    colon (:) delimited paths where one would expect to find experiment directories.
    
    Returns empty list if not set.
    """
    experiment_sources_env = os.environ.get("EXPERIMENT_SOURCES")
    
    if not experiment_sources_env:
        return []
    
    paths = []
    for path_str in experiment_sources_env.split(':'):
        path = Path(path_str)
        if path.exists() and path.is_dir():
            paths.append(path)
    
    return paths


EXPERIMENT_SOURCES = get_experiment_sources()

if EXPERIMENT_SOURCES:
    print("Using the following paths for sources of experiments:")
    for path in EXPERIMENT_SOURCES:
        print(path)


def get_analysis_experiments() -> List[Path]:
    """Get all experiment directories (directories starting with 'E-')."""
    experiments = []
    for source_path in EXPERIMENT_SOURCES:
        if source_path.exists() and source_path.is_dir():
            for item in source_path.iterdir():
                if item.is_dir() and item.name.startswith('E-'):
                    experiments.append(item)
    return experiments


# Lazy load analysis experiments
_analysis_experiments: Optional[List[Path]] = None


def analysis_experiments() -> List[Path]:
    """Get analysis experiments (lazy loaded)."""
    global _analysis_experiments
    if _analysis_experiments is None:
        _analysis_experiments = get_analysis_experiments()
    return _analysis_experiments
