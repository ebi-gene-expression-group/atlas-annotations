"""Experiment directory handling."""
from pathlib import Path
from typing import List, Dict
import xml.etree.ElementTree as ET
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
import directories


class ExperimentDirectory:
    """Represents an experiment directory."""
    
    def __init__(self, path: Path):
        self.path = path
    
    @property
    def accession(self) -> str:
        """Get experiment accession from directory name."""
        return self.path.name
    
    def get_configuration_xml(self) -> ET.Element:
        """Load and parse the configuration XML file."""
        config_file = self.path / f"{self.accession}-configuration.xml"
        tree = ET.parse(config_file)
        return tree.getroot()
    
    def get_array_designs(self) -> List[str]:
        """
        Get array designs from configuration XML.
        
        Only applies to microarray experiments.
        """
        # Check if this is a microarray experiment by looking at the path
        if 'microarray' not in str(self.path):
            return []
        
        try:
            config_xml = self.get_configuration_xml()
            # Find all array_design elements
            array_designs = []
            for elem in config_xml.iter('array_design'):
                if elem.text:
                    array_designs.append(elem.text.strip())
            return array_designs
        except Exception:
            return []


def get_all_experiment_directories() -> List[ExperimentDirectory]:
    """Get all experiment directories."""
    return [ExperimentDirectory(exp) for exp in directories.analysis_experiments()]


def get_all_array_designs() -> Dict[tuple, List[str]]:
    """
    Get all array designs grouped by experiment.
    
    Returns:
        Dictionary mapping (array_designs_tuple) to list of experiment accessions
    """
    result = {}
    
    for exp_dir in get_all_experiment_directories():
        array_designs = exp_dir.get_array_designs()
        if array_designs:
            key = tuple(array_designs)
            if key not in result:
                result[key] = []
            result[key].append(exp_dir.accession)
    
    return result
