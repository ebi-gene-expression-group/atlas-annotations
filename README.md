# Atlas Annotations (v1.3.0)


This is a repository for scripts that we use for retrieving annotations used by Atlas Solr searches and more.
It also stores the config of Atlas properties per species name and which public BioMart database we retrieve it from.

Version 1.3.0 was used for the November 2019 Atlas (bulk and single cell) releases.

### Dependencies
- Python 3.6+
- Python packages: `pip install -r requirements.txt`
- Various bash utilities, mysql
- Environment variable $ATLAS_PROD (see util/create_test_env.sh to work with this script)

We are in the process of detaching this from our direct filesystem dependencies. As such, the use of $ATLAS_PROD is being replaced
everywhere to point more specificly to the exact needs of each script.

### Entry points

`sh/ensembl/ensemblUpdate.sh`
the entry point to the annotations update process

`sh/atlas_species.sh`
Regenerate the species file based on annotation sources config

`python3 src/pipeline/retrieve/retrieve.py --validate-only`
Runs only the BioMart mapping verification for defined organisms (depends on the organisms file inside either
`annsrc` or the overriding `$ANNOTATION_SOURCES` path). These tests are automated in our internal Jenkins setup
under the `Ensembl Update` tab.

### Structure

#### ./annsrcs
Annotation source files describing the mapping of Atlas properties we want to foreign properties with sources of their retrieval

#### ./util
Tools that make the Atlas team's work easier, including scripts to automatically update the annotation sources

#### ./sh
Executables that the Atlas development team runs to update their annotations

#### ./src
Python source code

|  path  	|   what it does	|
|:-:	|:-:	|
|   `./src/pipeline/start.py`	|   entry point for fetching annotations	|
|   `./src/pipeline/is_ready/properties_adequate.py`	|  check annotation sources vs what we think needs to be in them (e.g. all array designs ) |
|   `./src/pipeline/retrieve`	|  fetch annotations - internals 	|
|  ` ./src/go/properties_from_owl_file.py`	|   Parse the go.owl for what we need	|
|   `./src/interpro/parse.py`	|   Parse the Interpro provided file	|
|  ` ./src/atlas/atlas_species.py`	|   Create the species config for the webapp	|
