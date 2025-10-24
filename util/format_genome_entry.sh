#!/usr/bin/env bash
# Usage: ./format_genome_entry.sh "saccharomyces_cerevisiae 4932 ensemblgenomes ftp://ftp.ensemblgenomes.org/pub/release-RELNO/fungi/fasta/saccharomyces_cerevisiae/dna/Saccharomyces_cerevisiae.R64-1-1.dna.toplevel.fa.gz ftp://ftp.ensemblgenomes.org/pub/release-RELNO/fungi/fasta/saccharomyces_cerevisiae/cdna/Saccharomyces_cerevisiae.R64-1-1.cdna.all.fa.gz ftp://ftp.ensemblgenomes.org/pub/release-RELNO/fungi/gtf/saccharomyces_cerevisiae/Saccharomyces_cerevisiae.R64-1-1.RELNO.gtf.gz R64-1-1"
# This script converts atlas-annotations/sh/gtf/genome_references.conf to YAML for nf-core/references piepline 
# Usage: ./format_genome_entries.sh input_file.txt
# Reads each line, skips comments or empty lines, and prints YAML blocks.

input_file="$1"

if [[ -z "$input_file" ]]; then
  echo "Usage: $0 input_file.txt"
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

  # Convert lowercase species name to capitalized form (e.g., Saccharomyces_cerevisiae)
  species_cap=$(echo "$species" | awk -F'_' '{print toupper(substr($1,1,1)) substr($1,2) "_" toupper(substr($2,1,1)) substr($2,2)}')

  # Convert ftp:// to https:// and adjust domain for ensemblgenomes → ensembl
  fasta_url_https=$(echo "$fasta_url" | sed 's|ftp://ftp.ensemblgenomes.org|https://ftp.ensembl.org|')
  gtf_url_https=$(echo "$gtf_url" | sed 's|ftp://ftp.ensemblgenomes.org|https://ftp.ensembl.org|')

  # Normalize source name
  if [[ "$source" == "ensemblgenomes" ]]; then
    source_name="Ensembl"
  else
    source_name=$(echo "$source" | awk '{print toupper(substr($1,1,1)) substr($1,2)}')
  fi

  # Print YAML entry
  cat <<EOF
- genome: $genome
  fasta: "$fasta_url_https"
  gtf: "$gtf_url_https"
  source_version: "${source_name}_RELNO"
  species: "$species_cap"
  source: "$source_name"
  # Add these fields to ensure index generation
  mito_name: "MT"
  macs_gsize: 12100000
EOF

done < "$input_file"

