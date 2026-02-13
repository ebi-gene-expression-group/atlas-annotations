"""BioMart API client for retrieving annotations."""
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from property import annotation_source
from util import combinators


def request(database_name: str, properties: Dict[str, str]) -> str:
    """
    Create a BioMart request URL with parameters.
    
    Args:
        database_name: Database name (ensembl, plants, etc.)
        properties: Query parameters
    
    Returns:
        Full request URL
    """
    base_url_map = {
        "metazoa": "https://metazoa.ensembl.org",
        "plants": "https://plants.ensembl.org",
        "fungi": "https://fungi.ensembl.org",
        "parasite": "https://parasite.wormbase.org",
        "protists": "https://protists.ensembl.org"
    }
    
    base = base_url_map.get(database_name, "https://www.ensembl.org")
    return base + "/biomart/martservice"


def get_as_xml(url: str, params: Dict[str, str]) -> Tuple[Optional[str], Optional[ET.Element]]:
    """
    Make HTTP request and parse as XML.
    
    Returns:
        (None, xml_element) on success
        (error_message, None) on failure
    """
    try:
        response = requests.get(url, params=params, timeout=(5, 1000))
        response.raise_for_status()
        
        xml_elem = ET.fromstring(response.text)
        return (None, xml_elem)
    except Exception as e:
        return (str(e), None)


def registry_request(annot_source: Path) -> Tuple[Optional[str], Optional[str]]:
    """Get registry request URL for annotation source."""
    error, database_name = annotation_source.get_value(annot_source, "databaseName")
    
    if error:
        return (error, None)
    
    return (None, request(database_name, {"type": "registry"}))


def available_marts_and_their_schemas(response_xml: ET.Element) -> Dict[str, str]:
    """Extract available marts and their schemas from registry XML."""
    marts = {}
    
    for elem in response_xml.findall('.//MartURLLocation'):
        database = elem.get('database')
        server_virtual_schema = elem.get('serverVirtualSchema')
        
        if database and server_virtual_schema:
            marts[database] = server_virtual_schema
    
    return marts


def lookup_available_marts_and_their_schemas(annot_source: Path) -> Tuple[Optional[str], Optional[Dict[str, str]]]:
    """
    Look up available marts and their schemas.
    
    Returns:
        (None, {mart: schema}) on success
        (error_message, None) on failure
    """
    error, url = registry_request(annot_source)
    if error:
        return (error, None)
    
    error, xml_elem = get_as_xml(url, {"type": "registry"})
    if error:
        return (error, None)
    
    marts = available_marts_and_their_schemas(xml_elem)
    return (None, marts)


def pick_most_appropriate_mart(expected_mart: str, marts: Dict[str, str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Pick the most appropriate mart from available marts.
    
    Returns:
        (None, schema) on success
        (error_message, None) on failure
    """
    # Try exact match first
    if expected_mart in marts:
        return (None, marts[expected_mart])
    
    # Try partial match
    for mart, schema in marts.items():
        if expected_mart in mart:
            return (None, schema)
    
    # No match found
    available = ', '.join(marts.keys())
    return (f"Could not determine serverVirtualSchema because expected mart {expected_mart} not found, available marts: {available}", None)


def lookup_server_virtual_schema(annot_source: Path) -> Tuple[Optional[str], Optional[str]]:
    """
    Look up the server virtual schema for an annotation source.
    
    Returns:
        (None, schema) on success
        (error_message, None) on failure
    """
    error, values = annotation_source.get_values(annot_source, ["software.name", "software.version"])
    
    if error:
        return (error, None)
    
    software_name, software_version = values
    expected_mart = f"{software_name}_mart_{software_version}"
    
    error, marts = lookup_available_marts_and_their_schemas(annot_source)
    if error:
        return (error, None)
    
    return pick_most_appropriate_mart(expected_mart, marts)


class Attribute:
    """Represents a BioMart attribute."""
    
    def __init__(self, property_name: str, name: str, kind: str, db_name: str, db_column: str):
        self.property_name = property_name
        self.name = name
        self.kind = kind
        self.db_name = db_name
        self.db_column = db_column
    
    @staticmethod
    def parse(tsv_line: str) -> Optional['Attribute']:
        """Parse an attribute from a TSV line."""
        cols = tsv_line.split('\t')
        
        if len(cols) == 7 and cols[4] == "html,txt,csv,tsv,xls":
            name = f"{cols[1]}/ {cols[2]}" if cols[2] else cols[1]
            return Attribute(cols[0], name, cols[3], cols[5], cols[6])
        
        return None


def attributes_request(annot_source: Path) -> Tuple[Optional[str], Optional[Tuple[str, Dict[str, str]]]]:
    """Create attributes request parameters."""
    error, values = annotation_source.get_values(annot_source, ["databaseName", "datasetName"])
    
    if error:
        return (error, None)
    
    database_name, dataset_name = values
    url = request(database_name, {})
    params = {"type": "attributes", "dataset": dataset_name}
    
    return (None, (url, params))


def lookup_attributes(annot_source: Path) -> Tuple[Optional[str], Optional[List[Attribute]]]:
    """
    Look up available attributes for an annotation source.
    
    Returns:
        (None, [Attribute]) on success
        (error_message, None) on failure
    """
    error, request_data = attributes_request(annot_source)
    if error:
        return (error, None)
    
    url, params = request_data
    
    try:
        response = requests.get(url, params=params, timeout=(5, 1000))
        response.raise_for_status()
        
        attributes = []
        for line in response.text.split('\n'):
            attr = Attribute.parse(line)
            if attr:
                attributes.append(attr)
        
        return (None, attributes)
    except Exception as e:
        return (str(e), None)


class BiomartAuxiliaryInfo:
    """Auxiliary information for BioMart requests."""
    
    def __init__(self, database_name: str, server_virtual_schema: str, dataset_name: str,
                 dataset_filters: Optional[Dict[str, str]] = None):
        self.database_name = database_name
        self.server_virtual_schema = server_virtual_schema
        self.dataset_name = dataset_name
        self.dataset_filters = dataset_filters or {}
    
    @staticmethod
    def get_for_annotation_source(annot_source: Path) -> Tuple[Optional[str], Optional['BiomartAuxiliaryInfo']]:
        """Get BioMart auxiliary info for an annotation source."""
        # Get required values
        error1, database_name = annotation_source.get_value(annot_source, "databaseName")
        error2, server_virtual_schema = lookup_server_virtual_schema(annot_source)
        error3, dataset_name = annotation_source.get_value(annot_source, "datasetName")
        
        # Get optional dataset filters
        dataset_filter_name = annotation_source.get_optional_value(annot_source, "datasetFilterName")
        dataset_filter_value = annotation_source.get_optional_value(annot_source, "datasetFilterValue")
        
        dataset_filters = {}
        if dataset_filter_name and dataset_filter_value:
            dataset_filters[dataset_filter_name] = dataset_filter_value
        
        # Check for errors
        if error1:
            return (error1, None)
        if error2:
            return (error2, None)
        if error3:
            return (error3, None)
        
        return (None, BiomartAuxiliaryInfo(
            database_name,
            server_virtual_schema,
            dataset_name,
            dataset_filters
        ))
    
    @staticmethod
    def get_map(annotation_sources: List[Path]) -> Tuple[Optional[List[str]], Optional[Dict[Path, 'BiomartAuxiliaryInfo']]]:
        """Get auxiliary info map for multiple annotation sources."""
        results = []
        for source in annotation_sources:
            error, info = BiomartAuxiliaryInfo.get_for_annotation_source(source)
            results.append((error, (source, info) if not error else None))
        
        error, success_list = combinators.combine(results)
        
        if error:
            return (error, None)
        else:
            return (None, dict(success_list))


def query_parameter(biomart_info: BiomartAuxiliaryInfo, filters: Dict[str, str],
                    attributes: List[str]) -> str:
    """Generate BioMart query XML."""
    # Build XML query
    query = ET.Element('Query')
    query.set('virtualSchemaName', biomart_info.server_virtual_schema)
    query.set('formatter', 'TSV')
    query.set('header', '0')
    query.set('uniqueRows', '1')
    query.set('count', '0')
    
    dataset = ET.SubElement(query, 'Dataset')
    dataset.set('name', biomart_info.dataset_name)
    dataset.set('interface', 'default')
    
    # Add filters
    all_filters = {**biomart_info.dataset_filters, **filters}
    for key, value in all_filters.items():
        filter_elem = ET.SubElement(dataset, 'Filter')
        filter_elem.set('name', key)
        filter_elem.set('value', value)
    
    # Add attributes
    for attr in attributes:
        attr_elem = ET.SubElement(dataset, 'Attribute')
        attr_elem.set('name', attr)
    
    return ET.tostring(query, encoding='unicode')


def biomart_request_params(biomart_info: BiomartAuxiliaryInfo, filters: Dict[str, str],
                            attributes: List[str]) -> Dict[str, str]:
    """Generate BioMart request parameters."""
    query = query_parameter(biomart_info, filters, attributes)
    return {
        "query": f'<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE Query>{query}'
    }


def fetch_from_biomart(aux: Dict[Path, BiomartAuxiliaryInfo], annot_source: Path,
                       filters: Dict[str, str], attributes: List[str]) -> Tuple[Optional[str], Optional[List[str]]]:
    """
    Fetch data from BioMart.
    
    Returns:
        (None, [lines]) on success
        (error_message, None) on failure
    """
    # Get auxiliary info
    if annot_source in aux:
        biomart_info = aux[annot_source]
    else:
        error, biomart_info = BiomartAuxiliaryInfo.get_for_annotation_source(annot_source)
        if error:
            return (error, None)
    
    # Build request
    url = request(biomart_info.database_name, {})
    params = biomart_request_params(biomart_info, filters, attributes)
    
    try:
        response = requests.get(url, params=params, timeout=(5, 1000))
        response.raise_for_status()
        
        if not response.text:
            return ("Received response with an empty body", None)
        
        lines = response.text.split('\n')
        return (None, lines)
    except Exception as e:
        return (str(e), None)
