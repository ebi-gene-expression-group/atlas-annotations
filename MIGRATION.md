# Migration Guide: Scala to Python Conversion

This document describes the conversion of all Scala/Ammonite scripts to Python and provides guidance for users migrating to the new Python-based version.

## What Changed

All 16 Scala/Ammonite scripts (`.sc` files) have been converted to Python (`.py` files):

| Old Scala Script | New Python Script |
|------------------|-------------------|
| `src/Directories.sc` | `src/directories.py` |
| `src/util/Combinators.sc` | `src/util/combinators.py` |
| `src/pipeline/Log.sc` | `src/pipeline/log.py` |
| `src/pipeline/Paths.sc` | `src/pipeline/paths.py` |
| `src/go/PropertiesFromOwlFile.sc` | `src/go/properties_from_owl_file.py` |
| `src/interpro/Parse.sc` | `src/interpro/parse.py` |
| `src/atlas/AtlasSpecies.sc` | `src/atlas/atlas_species.py` |
| `src/property/AnnotationSource.sc` | `src/property/annotation_source.py` |
| `src/property/AtlasProperty.sc` | `src/property/atlas_property.py` |
| `src/pipeline/retrieve/BioMart.sc` | `src/pipeline/retrieve/biomart.py` |
| `src/pipeline/retrieve/Tasks.sc` | `src/pipeline/retrieve/tasks.py` |
| `src/pipeline/retrieve/Transform.sc` | `src/pipeline/retrieve/transform.py` |
| `src/pipeline/retrieve/Retrieve.sc` | `src/pipeline/retrieve/retrieve.py` |
| `src/pipeline/Start.sc` | `src/pipeline/start.py` |
| `src/pipeline/is_ready/PropertiesAdequate.sc` | `src/pipeline/is_ready/properties_adequate.py` |
| `src/experiment/ExperimentDirectory.sc` | `src/experiment/experiment_directory.py` |

## Prerequisites

### Before (Scala/Ammonite)
- Java JDK 8+
- Ammonite REPL

### After (Python)
- Python 3.6 or higher
- pip (Python package manager)

## Installation

1. Install Python 3.6+ if not already installed:
   ```bash
   # On Ubuntu/Debian
   sudo apt-get install python3 python3-pip
   
   # On macOS
   brew install python3
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage Changes

### Shell Scripts (No Change Required)

All shell script entry points remain the same:

```bash
# Generate species file
sh/atlas_species.sh

# Update Ensembl annotations
sh/ensembl/ensemblUpdate.sh <ENSEMBL_REL> <ENSEMBLGENOMES_REL>

# Fetch GO/PO term mappings
sh/go/fetchGoIDToTermMappings.sh <outputDir>

# Fetch Interpro mappings
sh/interpro/fetchInterproIDToTypeTermMappings.sh <outputDir>
```

### Direct Python Invocation

If you were previously calling Ammonite scripts directly, update your commands:

**Before:**
```bash
amm -s src/atlas/AtlasSpecies.sc
amm -s src/pipeline/Start.sc
amm -s src/pipeline/retrieve/Retrieve.sc
```

**After:**
```bash
python3 src/atlas/atlas_species.py
python3 src/pipeline/start.py
python3 src/pipeline/retrieve/retrieve.py --validate-only
```

## Docker/Singularity

### Dockerfile
The `Dockerfile_base` has been updated to use Python 3.9 instead of the Ammonite image:

```dockerfile
FROM python:3.9-slim
```

### Singularity
The singularity script now references a Python image. For production use, consider building a custom image with all dependencies pre-installed.

## Environment Variables

All environment variables remain the same:
- `PATH_BIOENTITY_PROPERTIES` - Path to bioentity properties directory
- `ANNOTATION_SOURCES` - Colon-separated paths to annotation sources
- `EXPERIMENT_SOURCES` - Colon-separated paths to experiment directories (optional for some scripts)
- `ATLAS_PROD` - Atlas production directory (used by some wrapper scripts)

## Functional Changes

The Python scripts maintain the same functionality as the Scala scripts with these improvements:

1. **No JVM required** - Faster startup times, lower memory footprint
2. **Standard Python packaging** - Easier to install and distribute
3. **Better error messages** - More Pythonic error handling
4. **Type hints** - Better code documentation and IDE support
5. **Concurrent execution** - Uses Python's ThreadPoolExecutor for parallel BioMart requests

## Testing

Basic testing has been performed on:
- XML parsers (GO/PO and Interpro)
- Species file generation
- Property reading and validation

For production use, test with your actual data and configuration before deploying.

## Troubleshooting

### Import errors
Ensure you're running Python from the repository root directory:
```bash
cd /path/to/atlas-annotations
python3 src/atlas/atlas_species.py
```

### Missing dependencies
Install all required packages:
```bash
pip install -r requirements.txt
```

### Environment variable errors
The scripts require `PATH_BIOENTITY_PROPERTIES` to be set. For scripts that work with experiments, `EXPERIMENT_SOURCES` must also be set.

## Questions?

If you encounter issues or have questions about the migration, please open an issue on GitHub.
