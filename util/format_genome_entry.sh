#!/usr/bin/env bash
# Usage: ./format_genome_entries.sh input_file.txt ENSEMBL_RELNO ENSEMBLGENOMES_RELNO
# Example: ./format_genome_entries.sh genome_references.conf 112 60
#
# Reads each line, skips comments or empty lines, replaces RELNO with proper release numbers,
# and outputs YAML for each entry.
# This script converts atlas-annotations/sh/gtf/genome_references.conf to YAML for nf-core/references piepline 

input_file="$1"
ensembl_rel="$2"
ensemblgenomes_rel="$3"

if [[ -z "$input_file" || -z "$ensembl_rel" || -z "$ensemblgenomes_rel" ]]; then
  echo "Usage: $0 input_file.txt ENSEMBL_RELNO ENSEMBLGENOMES_RELNO"
  exit 1
fi

while IFS= read -r line; do
  # Skip empty lines or comments
  [[ -z "$line" || "$line" =~ ^# ]] && continue

  # Split into fields
  species=$(echo "$line" | awk '{print $1}')
  taxid=$(echo "$line" | awk '{print $2}')
  source=$(echo "$line" | awk '{print $3}')
  fasta_url=$(echo "$line" | awk '{print $4}')
  cdna_url=$(echo "$line" | awk '{print $5}')
  gtf_url=$(echo "$line" | awk '{print $6}')
  genome=$(echo "$line" | awk '{print $7}')

  # Determine which release to use based on FTP domain
  if [[ "$fasta_url" == *"ftp.ensemblgenomes.org"* ]]; then
    rel="$ensemblgenomes_rel"
    source_name="Ensembl"
    # convert ensemblgenomes FTP to ensembl HTTPS and replace RELNO
    fasta_url_mod=$(echo "$fasta_url" | sed "s|ftp://ftp.ensemblgenomes.org|https://ftp.ensembl.org|" | sed "s|RELNO|$rel|g")
    gtf_url_mod=$(echo "$gtf_url" | sed "s|ftp://ftp.ensemblgenomes.org|https://ftp.ensembl.org|" | sed "s|RELNO|$rel|g")
  elif [[ "$fasta_url" == *"ftp.ensembl.org"* ]]; then
    rel="$ensembl_rel"
    source_name="Ensembl"
    # convert ftp to https and replace RELNO
    fasta_url_mod=$(echo "$fasta_url" | sed "s|ftp://|https://|" | sed "s|RELNO|$rel|g")
    gtf_url_mod=$(echo "$gtf_url" | sed "s|ftp://|https://|" | sed "s|RELNO|$rel|g")
  else
    echo "Warning: Unknown FTP source for $species — skipping."
    continue
  fi

  # Capitalize species nicely (e.g. saccharomyces_cerevisiae → Saccharomyces_cerevisiae)
  species_cap=$(echo "$species" | awk -F'_' '{print toupper(substr($1,1,1)) substr($1,2) "_" toupper(substr($2,1,1)) substr($2,2)}')

  # Print YAML entry
  cat <<EOF
- genome: $genome
  fasta: "$fasta_url_mod"
  gtf: "$gtf_url_mod"
  source_version: "${source_name}_${rel}"
  species: "$species_cap"
  source: "$source_name"
  # Add these fields to ensure index generation
  mito_name: "MT"
  macs_gsize: 12100000
EOF

done < "$input_file"
