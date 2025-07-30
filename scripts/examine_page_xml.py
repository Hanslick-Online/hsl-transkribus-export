#!/usr/bin/env python3
"""
Script to examine PAGE XML content from Transkribus for any collection and document
"""

import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlencode, urlparse
import sys
import os
import argparse

def get_page_ids_from_mets(collection_id, document_id):
    """Extract PAGE XML file IDs from METS file"""
    mets_file_path = f"./mets/{collection_id}/{document_id}_mets.xml"

    if not os.path.exists(mets_file_path):
        print(f"METS file not found: {mets_file_path}")
        return []

    try:
        tree = ET.parse(mets_file_path)
        root = tree.getroot()

        # Define namespace
        ns = {'ns3': 'http://www.loc.gov/METS/', 'ns2': 'http://www.w3.org/1999/xlink'}

        page_ids = []

        # Find all PAGEXML files
        pagexml_files = root.findall('.//ns3:fileGrp[@ID="PAGEXML"]/ns3:file', ns)

        for file_elem in pagexml_files:
            # Get the FLocat element with the URL
            fptr = file_elem.find('ns3:FLocat', ns)
            if fptr is not None:
                href = fptr.get('{http://www.w3.org/1999/xlink}href')
                if href:
                    # Extract the ID parameter from the URL
                    parsed_url = urlparse(href)
                    if 'id=' in parsed_url.query:
                        # Extract id parameter
                        params = dict(param.split('=') for param in parsed_url.query.split('&') if '=' in param)
                        if 'id' in params:
                            page_ids.append(params['id'])

        print(f"Found {len(page_ids)} page IDs in METS file")
        return page_ids

    except ET.ParseError as e:
        print(f"Error parsing METS file: {e}")
        return []
    except Exception as e:
        print(f"Error reading METS file: {e}")
        return []

def fetch_page_xml(file_id):
    """Fetch PAGE XML from Transkribus by file ID"""
    url = f"https://files.transkribus.eu/Get?id={file_id}"

    try:
        print(f"Fetching PAGE XML from: {url}")
        response = requests.get(url)
        response.raise_for_status()

        # Parse XML
        root = ET.fromstring(response.content)
        return root, response.content

    except requests.RequestException as e:
        print(f"Error fetching PAGE XML: {e}")
        return None, None
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        return None, None

def extract_text_content(root):
    """Extract text content from PAGE XML"""

    # Define namespaces
    namespaces = {
        'page': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15',
        'page2019': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15'
    }

    print("=== PAGE XML STRUCTURE ===")
    print(f"Root element: {root.tag}")
    print(f"Root attributes: {root.attrib}")

    # Find all text regions
    text_regions = []
    text_regions.extend(root.findall('.//page:TextRegion', namespaces))
    text_regions.extend(root.findall('.//page2019:TextRegion', namespaces))

    print(f"\nFound {len(text_regions)} text regions")

    for i, region in enumerate(text_regions):
        print(f"\n--- Text Region {i+1} ---")
        print(f"ID: {region.get('id', 'N/A')}")
        print(f"Type: {region.get('type', 'N/A')}")
        print(f"Custom: {region.get('custom', 'N/A')}")

        # Find text lines in this region
        text_lines = []
        text_lines.extend(region.findall('.//page:TextLine', namespaces))
        text_lines.extend(region.findall('.//page2019:TextLine', namespaces))

        print(f"Text lines: {len(text_lines)}")

        for j, line in enumerate(text_lines):
            # Find Unicode text content
            unicode_elems = []
            unicode_elems.extend(line.findall('.//page:Unicode', namespaces))
            unicode_elems.extend(line.findall('.//page2019:Unicode', namespaces))

            for unicode_elem in unicode_elems:
                if unicode_elem.text:
                    print(f"  Line {j+1}: {unicode_elem.text}")

    return text_regions

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Examine PAGE XML content from Transkribus')
    parser.add_argument('collection_id', help='Collection ID')
    parser.add_argument('document_id', help='Document ID')
    parser.add_argument('--debug-dir', default='./debug', help='Directory to save debug files (default: ./debug)')

    args = parser.parse_args()

    # Create debug directory if it doesn't exist
    os.makedirs(args.debug_dir, exist_ok=True)

    # Get page IDs from METS file
    page_ids = get_page_ids_from_mets(args.collection_id, args.document_id)

    if not page_ids:
        print(f"No page IDs found for collection {args.collection_id}, document {args.document_id}")
        return

    for i, page_id in enumerate(page_ids):
        print(f"\n{'='*60}")
        print(f"EXAMINING PAGE {i+1} (ID: {page_id})")
        print(f"{'='*60}")

        root, raw_xml = fetch_page_xml(page_id)

        if root is not None and raw_xml is not None:
            # Save raw XML for examination in debug folder
            filename = os.path.join(args.debug_dir, f"page_{i+1}_{page_id}.xml")
            with open(filename, 'wb') as f:
                f.write(raw_xml)
            print(f"Saved raw XML to: {filename}")

            # Extract and display text content
            extract_text_content(root)
        else:
            print(f"Failed to fetch PAGE {i+1}")

if __name__ == "__main__":
    main()
