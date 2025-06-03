#!/usr/bin/env python3

from ftplib import FTP
import argparse, re, os, sys

def parse_url(url):
    """
    Parses a complete ftp URL into server, path and file name.
    """
    match = re.search("ftp://([a-z\.]*)/(.*)$", url)
    server = match.group(1)
    path_tokens = match.group(2).split("/")
    return server, "/"+"/".join(path_tokens[:-1]), path_tokens[-1]

def check_connection(server, corrected_url, path, file):
    ftp = FTP(server)
    ftp.login()
    try:
        ftp.cwd(path)
    except Exception as e:
        print("Error accessing path " + path + ": " + str(e))
        sys.exit(1)
    files_listed = []
    ftp.retrlines('NLST', files_listed.append)
    if file in files_listed:
        print("URL found:")
        print(corrected_url)
        sys.exit(0)
    else:
        print("Not found: "+path+'/'+file)
        print("Possible alternatives are:")
        for file_l in files_listed:
            if "gtf" in file_l:
                print("- "+file_l)
        sys.exit(1)
        


parser = argparse.ArgumentParser(description='Check Genome, Transcriptome and GTF URLs for organism and release based on genome_references.conf file.')
parser.add_argument('--organism', help='Organism to validate for')
parser.add_argument('--release', help='release number')
args = parser.parse_args()

genome_references_path = os.path.abspath(os.path.dirname(sys.argv[0]))+"/genome_references.conf"

for line in open(genome_references_path, 'r'):
    (organism, tax_id, genus, genome_fa, cdna_fa, gtf_fa, misc) = line.split()
    if organism == args.organism:
        for fa in genome_fa, cdna_fa, gtf_fa:
            corrected_fa = fa.replace("RELNO", args.release)
            server, path, file = parse_url(corrected_fa)
            check_connection(server, corrected_fa, path, file)
        
