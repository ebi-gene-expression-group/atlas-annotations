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


parser = argparse.ArgumentParser(description='Check GTF URLs for organism and release based on gxa_references.conf file.')
parser.add_argument('--organism', help='Organism to validate for')
# parser.add_argument('--source', help='ensembl or wbps')
parser.add_argument('--release', help='release number')
args = parser.parse_args()

gxa_references_path = os.path.abspath(os.path.dirname(sys.argv[0]))+"/gxa_references.conf"

for line in open(gxa_references_path, 'r'):
    (organism, url) = line.split()
    if organism == args.organism:
        corrected_url = url.replace("RELNO", args.release)
        server, path, gtf_file = parse_url(corrected_url)
        ftp = FTP(server)
        ftp.login()
        try:
            ftp.cwd(path)
        except Error:
            print("Path "+path+" not found!")
            sys.exit(1)
        files_listed = []
        ftp.retrlines('NLST', files_listed.append)
        if gtf_file in files_listed:
            print("URL found:")
            print(corrected_url)
            sys.exit(0)
        else:
            print("Not found: "+path+'/'+gtf_file)
            print("Possible alternatives are:")
            for file_l in files_listed:
                if "gtf" in file_l:
                    print("- "+file_l)
            sys.exit(1)
