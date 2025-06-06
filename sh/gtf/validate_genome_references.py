#!/usr/bin/env python3

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
    ftp = FTP(server)
    ftp.login()
    try:
        ftp.cwd(path)
    except Exception as e:
        print("Error: For " + organism + " error accessing path " + path + ": " + str(e))
        fail = True
    files_listed = []
    ftp.retrlines('NLST', files_listed.append)
    if file in files_listed:
        print("URL found:")
        print(corrected_url)
    else:
        print("Error: For " + organism + " file not found: "+path+'/'+file)
        print("Possible alternatives are:")
        for file_l in files_listed:
            if "gtf" in file_l:
                print("- "+file_l)
        fail = True
        


parser = argparse.ArgumentParser(description='Check Genome, Transcriptome and GTF URLs for organism and release based on genome_references.conf file.')
parser.add_argument('--release', help='release number')
args = parser.parse_args()

genome_references_path = os.path.abspath(os.path.dirname(sys.argv[0]))+"/genome_references.conf"

for line in open(genome_references_path, 'r'):
    line = line.strip()  # Remove leading/trailing whitespace
    if not line or line.startswith('#'):
        continue
        
    (organism, tax_id, genus, genome_fa, cdna_fa, gtf_fa, misc) = line.split()
    for fa in genome_fa, cdna_fa, gtf_fa:
        corrected_fa = fa.replace("RELNO", args.release)
        server, path, file = parse_url(corrected_fa)
        check_connection(organism, server, corrected_fa, path, file)

if fail == True:
    print("Validation ended up in one or more errors.")
    sys.exit(1)
else:
    if fail == True:
    print("Validation completed successfully.")
        
