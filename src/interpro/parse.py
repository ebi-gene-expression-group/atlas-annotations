#!/usr/bin/env python3
"""
Input: location of the interpro file downloaded from their FTP site
we extract from such lines only: <interpro id="IPR000003" protein_count="1309" short_name="Retinoid-X_rcpt/HNF4" type="Family">
Stdout: <interpro_name><tab><interpro id><tab><interpro description>
"""
import sys
import xml.etree.ElementTree as ET


def parse(file_location):
    """Parse interpro XML file and extract relevant information."""
    results = []
    
    try:
        # Parse XML incrementally to handle large files
        for event, elem in ET.iterparse(file_location, events=('start', 'end')):
            if event == 'start' and elem.tag == 'interpro':
                interpro_id = elem.get('id', '')
                interpro_type = elem.get('type', '')
                interpro_attributes = (interpro_id, interpro_type)
            elif event == 'end' and elem.tag == 'name':
                if elem.text:
                    name = elem.text
                    results.append(f"{name}\t{interpro_attributes[0]}\t{interpro_attributes[1]}")
                # Clear element to save memory
                elem.clear()
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}", file=sys.stderr)
        sys.exit(1)
    
    return results


def main(file_location):
    """Main entry point for parsing interpro file."""
    results = parse(file_location)
    for result in results:
        print(result)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: parse.py <fileLocation>", file=sys.stderr)
        sys.exit(1)
    
    main(sys.argv[1])
