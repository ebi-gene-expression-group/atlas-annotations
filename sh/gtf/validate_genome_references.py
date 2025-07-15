#!/usr/bin/env python3

# This script validates FTP URLs from a genome reference config file for Ensembl and EnsemblGenomes.
# It checks FTP connectivity, directory existence, and file presence for genome, cDNA, and GTF files.

from ftplib import FTP
import argparse, re, os, sys

fail = False
def parse_url(url):
    """
    Parses a complete ftp URL into server, path and file name.
    """
    match = re.search("ftp://([a-z\.]*)/(.*)$", url)
    server = match.group(1)
    path_tokens = match.group(2).split("/")
    return server, "/"+"/".join(path_tokens[:-1]), path_tokens[-1]

def check_connection(organism, server, corrected_url, path, file):
    global fail
    ftp = FTP(server)
    ftp.login()
    
    try:
        ftp.cwd(path)
    except Exception as e:
        if "550 Failed to change directory" in str(e):
            parent_path = '/'.join(path.rstrip('/').split('/')[:-2])

            GTF_EXTENSIONS = (".gtf", ".gtf.gz")
            if file.lower().endswith(GTF_EXTENSIONS):
                parent_path = '/'.join(path.rstrip('/').split('/')[:-1])
            
            print(f"Organism {organism} not found. URL {server}{path} is incorrect.")
            
            species_listed = []
            
            try:
                ftp.cwd(parent_path)
                ftp.retrlines('NLST', species_listed.append)

                print("Possible species name alternatives are:")
                for file_l in species_listed:
                    if file_l.startswith(organism.split("_")[0]):
                        print(f"- {file_l}")
            except Exception as e2:
                print(f"Error accessing parent directory: {str(e2)}")
        else:
            print(f"Error: For {organism}, error accessing path {path}: {str(e)}")
        fail = True
        ftp.quit()
        return fail

    # If cwd succeeded, list files and check presence
    files_listed = []
    ftp.retrlines('NLST', files_listed.append)

    if file in files_listed:
        print("URL found:")
        print(corrected_url)
    else:
        print(f"Error: For {organism}, file not found: {path}/{file}")
        print("Possible alternatives are:")
        for file_l in files_listed:
            if file.split(".")[-1] in file_l:
                print(f"- {file_l}")
        fail = True

    ftp.quit()


parser = argparse.ArgumentParser(description='Check Genome, Transcriptome and GTF URLs for organism and release based on genome_references.conf file.')

parser.add_argument(
    '--ensembl',
    required=True,
    type=int,
    help='Ensembl release number (required, integer)'
)

parser.add_argument(
    '--ensemblgenomes',
    required=True,
    type=int,
    help='EnsemblGenomes release number (required, integer)'
)

args = parser.parse_args()

genome_references_path = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), "genome_references.conf")

for line in open(genome_references_path, 'r'):
    line = line.strip()  # Remove leading/trailing whitespace
    if not line or line.startswith('#'):
        continue
        
    (organism, tax_id, resource, genome_fa, cdna_fa, gtf_fa, misc) = line.split()

    if resource == "ensembl":
        release_no = args.ensembl
    elif resource == "ensemblgenomes":
        release_no = args.ensemblgenomes
    else:
        print("Incorrect resource ", resource, " found, skipping...")
        fail = True    
    
    for fa in genome_fa, cdna_fa, gtf_fa:
        corrected_fa = fa.replace("RELNO", release_no)
        server, path, file = parse_url(corrected_fa)
        check_connection(organism, server, corrected_fa, path, file)

if fail:
    print("Validation ended up in one or more errors.")
    sys.exit(1)
else:
    print("Validation completed successfully.")
        
