#!/usr/bin/env python3
"""
Input: location of go.owl or po.owl downloaded from http://geneontology.org/ontology/go.owl
<owl:Class>
    <rdfs:label>embryo proper</rdfs:label>
    <oboInOwl:hasAlternativeId>GO:0019952</oboInOwl:hasAlternativeId>
    <oboInOwl:hasAlternativeId>GO:0050876</oboInOwl:hasAlternativeId>
    <oboInOwl:id>GO:0000003</oboInOwl:id>
</owl:Class>

//alternativeIds output
GO:0019952\tGO:0000003
GO:0050876\tGO:0000003

//terms output
GO:0000003\tembryo proper
"""
import sys
import xml.etree.ElementTree as ET


def parse(property_namespace, property_name, file_location):
    """
    Parse OWL file and extract specified properties.
    
    Args:
        property_namespace: The XML namespace prefix (e.g., 'rdfs', 'oboInOwl')
        property_name: The property name (e.g., 'label', 'hasAlternativeId')
        file_location: Path to the OWL file
    
    Returns:
        List of tuples (id, property_value)
    """
    results = []
    current_id = None
    properties = []
    in_class = False
    reading_id = False
    reading_property = False
    current_text = []
    
    # Define namespace mappings
    namespaces = {
        'owl': 'http://www.w3.org/2002/07/owl#',
        'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
        'oboInOwl': 'http://www.geneontology.org/formats/oboInOwl#'
    }
    
    # Build the full tag names
    class_tag = f"{{{namespaces['owl']}}}Class"
    id_tag = f"{{{namespaces['oboInOwl']}}}id"
    property_tag = f"{{{namespaces.get(property_namespace, '')}}}{property_name}"
    
    try:
        for event, elem in ET.iterparse(file_location, events=('start', 'end')):
            if event == 'start':
                if elem.tag == class_tag:
                    in_class = True
                    current_id = None
                    properties = []
                elif in_class and elem.tag == id_tag:
                    reading_id = True
                elif in_class and elem.tag == property_tag:
                    reading_property = True
            
            elif event == 'end':
                if elem.tag == class_tag:
                    # End of class - save results
                    if current_id and properties:
                        for prop in properties:
                            results.append((current_id, prop))
                    in_class = False
                    current_id = None
                    properties = []
                    # Clear element to save memory
                    elem.clear()
                elif elem.tag == id_tag and reading_id:
                    if elem.text:
                        current_id = elem.text.strip()
                    reading_id = False
                elif elem.tag == property_tag and reading_property:
                    if elem.text:
                        properties.append(elem.text.strip())
                    reading_property = False
    
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}", file=sys.stderr)
        sys.exit(1)
    
    return results


def terms(file_location):
    """Extract term labels from OWL file."""
    results = parse('rdfs', 'label', file_location)
    for go_id, term_text in results:
        print(f"{go_id}\t{term_text}")


def alternative_ids(file_location):
    """Extract alternative ID mappings from OWL file."""
    results = parse('oboInOwl', 'hasAlternativeId', file_location)
    # Swap the tuple order for alternative IDs
    for go_id, alt_id in results:
        print(f"{alt_id}\t{go_id}")


def main():
    """Main entry point."""
    if len(sys.argv) != 3:
        print("Usage: properties_from_owl_file.py <terms|alternativeIds> <fileLocation>", file=sys.stderr)
        sys.exit(1)
    
    what = sys.argv[1]
    file_location = sys.argv[2]
    
    if what == 'terms':
        terms(file_location)
    elif what == 'alternativeIds':
        alternative_ids(file_location)
    else:
        print("Usage: properties_from_owl_file.py <terms|alternativeIds> <fileLocation>", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
